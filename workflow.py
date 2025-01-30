#!/usr/bin/env python

from pathlib import Path
from time import sleep
import sys
import csv
import os
import json
import re as regex
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import AzureOpenAI
from markitdown import MarkItDown
from tqdm import tqdm

import dotenv
dotenv.load_dotenv(".env")


NOTETAKING_PROMPT = (Path(__file__).parent / "prompts/notetaking.txt").read_text()
METADATA_PROMPT = (Path(__file__).parent / "prompts/metadata.txt").read_text()
FOR_CODE_PROMPT = (Path(__file__).parent / "prompts/for_code.txt").read_text()
FUNDING_SOURCE_PROMPT = (Path(__file__).parent / "prompts/funding_source.txt").read_text()
AFFILIATIONS_PROMPT = (Path(__file__).parent / "prompts/affiliations.txt").read_text()
OUTPUT_PROMPT = (Path(__file__).parent / "prompts/output_table.txt").read_text()
REPORT_PROMPT = (Path(__file__).parent / "prompts/report.txt").read_text()

def chunk_file_content(content:str, chunk_size:int=8192, overlap_size:int = 256) -> list[str]:
    # Chunk the content into chunks of maximum chunk_size, with overlapping regions of upto overlap_size (breaking at word boundaries)
    chunks = []
    start = 0
    end = 0
    while end < len(content):
        end = start + chunk_size
        while end < len(content) and content[end] != ' ':
            end += 1
        chunks.append(content[start:end])
        start = end - overlap_size
        ## Find start of next word
        while start < len(content) and content[start] == ' ':
            start += 1

    return chunks


def run_prompt(client: AzureOpenAI, model: str, system_prompt:str, user_prompt:str, json_response:bool = False) -> str:
    retries = 10
    while retries > 0:
        try:
            output_type = { "type": "json_object" } if json_response else { "type": "text" }
            completion = client.chat.completions.create(
                model=model,
                response_format=output_type,
                messages=[
                    { "role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response = completion.choices[0].message.content
            if response is not None and len(response) > 0:
                return response
            retries -= 1
        except Exception as e:
            msg = f"{e}"
            if "429" in msg:
                sleep(10)
                retries -= 1
            else: 
                retries -= 2
                sleep(1)
            if retries <= 0:
                raise e
    raise Exception("Failed to get response - too many failed attempts to run prompt")

def parse_file(file: Path) -> str:
    try:
        md = MarkItDown()
        result = md.convert(f"{file}")
        return result.text_content
    except Exception as e:
        print(f"[{file.stem}] Failed to parse PDF: {e}")
        return None


def get_metadata(content:str, client: AzureOpenAI, model: str) -> dict:
    response = run_prompt(client, model, METADATA_PROMPT, content, json_response=True)
    return json.loads(response)

def get_research_code(content:str, client: AzureOpenAI, model: str) -> dict:
    response = run_prompt(client, model, FOR_CODE_PROMPT, content, json_response=True)
    return json.loads(response)

def get_funding_source(content:str, client: AzureOpenAI, model: str) -> dict:
    response = run_prompt(client, model, FUNDING_SOURCE_PROMPT, content, json_response=True)
    return json.loads(response)

def get_affiliations(content:str, client: AzureOpenAI, model: str) -> dict:
    response = run_prompt(client, model, AFFILIATIONS_PROMPT, content, json_response=True)
    return json.loads(response)


def process_file(file: Path, interim_path: Path, output_path:Path, client: AzureOpenAI, notetaking_model: str, interpretation_model: str, worker_executor:ThreadPoolExecutor = None, force_update:bool = False, progress_bar:tqdm = None) -> tuple[bool, dict]:
    metadata = None
    try:
        ## Step 0: Parse the source file
        print(f"[{file.stem}] Processing")
        interim_file = interim_path / (file.stem + ".md")
        if force_update or not interim_file.exists():
            print(f"[{file.stem}] Parsing source")
            source_md = parse_file(file)
            if source_md is None: 
                raise Exception("Failed to parse source file")
            
            with open(interim_file, "w") as f:
                f.write(source_md)

        ## Step 1: Generate Notes
        content = interim_file.read_text()
        chunks = chunk_file_content(content)
        notes_file = interim_path / (file.stem + "_notes.md")
        notes_content = ""
        if force_update or not notes_file.exists() or notes_file.stat().st_size == 0:
            print(f"[{file.stem}] Writing Notes")
            with open(notes_file, "w") as f:
                chunk_num = 0
                chunk_futures = []
                for chunk in chunks:
                    chunk_futures.append(worker_executor.submit(run_prompt, client, notetaking_model, NOTETAKING_PROMPT, chunk, False))
                for chunk_future in chunk_futures:
                    chunk_num += 1
                    response = chunk_future.result()
                    f.write(f"# Chunk {chunk_num}\n\n")
                    f.write(f"{response}\n\n")
                    notes_content += f"# Chunk {chunk_num}\n\n{response}\n\n"
        else: 
            notes_content = notes_file.read_text()
            
            
        if notes_content == "" or notes_content is None:
            raise Exception("Failed to generate notes")
        
        ## Step 2: Determine the Metadata, Research Code, Funding sources, and affiliaitons in the paper
        metadata_file = interim_path / (file.stem + "_metadata.json")
        research_code_file = interim_path / (file.stem + "_research_code.json")
        funding_source_file = interim_path / (file.stem + "_funding_source.json")
        affiliations_file = interim_path / (file.stem + "_affiliations.json")

        # NB: Metadata defined above the try - to enable the error handling to capture the metadata if it's available
        research_code = None
        funding_source = None
        affiliations = None
        if force_update or not metadata_file.exists() or metadata_file.stat().st_size == 0 or not research_code_file.exists() or research_code_file.stat().st_size == 0 or not funding_source_file.exists() or funding_source_file.stat().st_size == 0 or not affiliations_file.exists() or affiliations_file.stat().st_size == 0:
            print(f"[{file.stem}] Analysing Notes")
            metadata_future = worker_executor.submit(get_metadata, notes_content, client, interpretation_model)
            research_code_future = worker_executor.submit(get_research_code, notes_content, client, interpretation_model)
            funding_source_future = worker_executor.submit(get_funding_source, notes_content, client, interpretation_model)
            affiliations_future = worker_executor.submit(get_affiliations, notes_content, client, interpretation_model)

            metadata = metadata_future.result()
            with open(metadata_file, "w") as f:
                f.write(json.dumps(metadata, indent=2))

            research_code = research_code_future.result()
            with open(research_code_file, "w") as f:
                f.write(json.dumps(research_code, indent=2))

            funding_source = funding_source_future.result()
            with open(funding_source_file, "w") as f:
                f.write(json.dumps(funding_source, indent=2))

            affiliations = affiliations_future.result()
            with open(affiliations_file, "w") as f:
                f.write(json.dumps(affiliations, indent=2))
        else: 
            metadata = json.loads(metadata_file.read_text())
            research_code = json.loads(research_code_file.read_text())
            funding_source = json.loads(funding_source_file.read_text())
            affiliations = json.loads(affiliations_file.read_text())

        if metadata is None or research_code is None or funding_source is None or affiliations is None:
            raise Exception("Failed to generate metadata, research code, funding source, or affiliations, or one of the existing files is blank")

        ## Step 3: Generate Report
        report_file = output_path / (file.stem + "_report.md")
        analysis_content = f"## Metadata\n\n{json.dumps(metadata, indent=2)}\n\n## Research Code\n\n{json.dumps(research_code, indent=2)}\n\n## Funding Source\n\n{json.dumps(funding_source, indent=2)}\n\n## Affiliations\n\n{json.dumps(affiliations, indent=2)}\n\n"
        if force_update or not report_file.exists() or report_file.stat().st_size == 0:
            if force_update or not report_file.exists():
                print(f"[{file.stem}] Generating Report")
                with open(report_file, "w") as f:
                    response = run_prompt(client, interpretation_model, REPORT_PROMPT, analysis_content, False)
                    f.write(response)

        ## Step 3: Return Table Info
        data = {}
        data["file"] = file.stem
        data["title"] = metadata["title"]
        data["journal"] = metadata["journal"]
        data["authors"] = metadata["authors"]
        data["for_code1"] = {
            "code": research_code["for"]["for4"]["code"],
            "category": research_code["for"]["for4"]["category"],
            "description": research_code["for"]["for4"]["description"],
            "reasoning": research_code["for"]["for4"]["reasoning"]
        }
        if "candidates" in research_code:
            if len(research_code["candidates"]) > 0:
                candidate = research_code["candidates"][0]
                if type(candidate) == dict and "for4" in candidate:
                    data["for_code2"] = {
                        "code": candidate["for4"]["code"],
                        "category": candidate["for4"]["category"],
                        "description": candidate["for4"]["description"],
                        "reasoning": candidate["for4"]["reasoning"]
                    }
                elif type(candidate) is str and candidate.isnumeric():
                    data["for_code2"] = {
                        "code": candidate,
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }
                else: 
                    data["for_code2"] = {
                        "code": "",
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }            
            if len(research_code["candidates"]) > 1:
                candidate = research_code["candidates"][1]
                if type(candidate) == dict and "for4" in candidate:
                    data["for_code3"] = {
                        "code": candidate["for4"]["code"],
                        "category": candidate["for4"]["category"],
                        "description": candidate["for4"]["description"],
                        "reasoning": candidate["for4"]["reasoning"]
                    }
                elif type(candidate) is str and candidate.isnumeric():
                    data["for_code3"] = {
                        "code": candidate,
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }
                else: 
                    data["for_code3"] = {
                        "code": "",
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }    

            if len(research_code["candidates"]) > 2:
                candidate = research_code["candidates"][2]
                if type(candidate) == dict and "for4" in candidate:
                    data["for_code4"] = {
                        "code": candidate["for4"]["code"],
                        "category": candidate["for4"]["category"],
                        "description": candidate["for4"]["description"],
                        "reasoning": candidate["for4"]["reasoning"]
                    }
                elif type(candidate) is str and candidate.isnumeric():
                    data["for_code4"] = {
                        "code": candidate,
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }
                else: 
                    data["for_code4"] = {
                        "code": "",
                        "category": "",
                        "description": "",
                        "reasoning": ""
                    }   
        data["funding_sources"] = {
            "sources": funding_source["source"],
            "reasoning": funding_source["reasoning"]
        }
        latrobe_affiliations = [ item for item in affiliations["affiliations"] if item["islatrobe"] == True]
        non_latrobe_affiliations = [ item for item in affiliations["affiliations"] if item["islatrobe"] == False]
        data["latrobe_affiliated"] = len(latrobe_affiliations) > 0
        data["latrobe_affiliations"] = [ { "name": item["name"], "reasoning": item["reasoning"] } for item in latrobe_affiliations ]
        data["non_latrobe_affiliations"] = [ { "name": item["name"], "reasoning": item["reasoning"] } for item in non_latrobe_affiliations ]
        print(f"[{file.stem}] Done")
        if progress_bar is not None:
            progress_bar.update(1)
        return (True, data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[{file.stem}] Error: {e}")
        if progress_bar is not None:
            progress_bar.update(1)
        data = {}
        data["file"] = file.stem
        data["title"] = metadata["title"]
        data["journnal"] = metadata["journal"]
        data["authors"] = metadata["authors"]
        data["error"] = f"{e}"
        return (False, data)



def main(args: dict[str, str]) -> None: 

    if args.get("--help", False):
        print("Usage: ./workflow.py <args>")
        print("Arguments:")
        print("--openai-key=<key> : OpenAI API Key")
        print("--openai-endpoint=<endpoint> : OpenAI Endpoint")
        print("--openai-api-version=<version> : OpenAI API Version")
        print("--notetaking-model=<model> : AI Model deployment to use for the notetaking phase of the process")
        print("--interpretation-model=<model> : AI Model deployment to use for the interpretation phase of the process")
        print("--filter=<regex> : Filter files based on a regex pattern")
        print("--source-dir=<dir> : Source Directory (where the source PDFs are stored)")
        print("--interim-dir=<dir> : Interim Directory (where the interim files are stored)")
        print("--output-dir=<dir> : Output Directory (where the final reports are stored)")
        print("--force-update : Force Updating all files (default: false) - will reprocess all files if set, otherwise will only process files that have not been processed")
        print("--concurrency=<int> : File Concurrency (default: 4) - Number of files to process concurrently")
        print("--workers=<int> : Worker Concurrency (default: 8) - Number of workers to allocate to performing tasks within the file processed (eg. note taking, analysis, etc...)")
        print("--max-files=<int> : Maximum number of files to process (default: 0) - 0 means all files")
        return
    

    openai_key = args.get("--openai-key", os.getenv("AZURE_OPENAI_API_KEY"))
    if openai_key is None:
        print("Please provide an OpenAI key using the --openai-key flag or in a .env file with the key OPENAI_KEY")
        return
    
    openai_endpoint = args.get("--openai-endpoint", os.getenv("AZURE_OPENAI_ENDPOINT"))
    if openai_endpoint is None:
        print("Please provide an OpenAI endpoint using the --openai-endpoint flag or in a .env file with the key OPENAI_ENDPOINT")
        return
    
    openai_api_version = args.get("--openai-api-version", os.getenv("AZURE_OPENAI_API_VERSION"))
    if openai_api_version is None:
        openai_api_version = "2024-02-15-preview"

    notetaking_model = args.get("--notetaking-model", os.getenv("NOTETAKING_MODEL"))
    if notetaking_model is None:
        notetaking_model = "gpt-4o-mini"
    
    interpretation_model = args.get("--interpretation-model", os.getenv("INTERPRETATION_MODEL"))
    if interpretation_model is None:
        interpretation_model = "gpt-4o"

    client = AzureOpenAI(
        api_key=openai_key,
        azure_endpoint=openai_endpoint,
        api_version=openai_api_version,
    )

    source_dir = args.get("--source-dir", os.getenv("SOURCE_DIR"))
    if source_dir is None:
        source_dir = "source"
    
    interim_dir = args.get("--interim-dir", os.getenv("INTERIM_DIR"))
    if interim_dir is None:
        interim_dir = "interim"
    
    output_dir = args.get("--output-dir", os.getenv("OUTPUT_DIR"))
    if output_dir is None:
        output_dir = "output"


    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Source directory {source_dir} does not exist")
        return
    
    interim_path = Path(interim_dir)
    if not interim_path.exists():
        interim_path.mkdir(parents=True, exist_ok=True)

    output_path = Path(output_dir)
    if not output_path.exists():
        output_path.mkdir(parents=True, exist_ok=True)

    force_update = args.get("--force-update", os.getenv("FORCE_UPDATE", False))
    max_files = int(args.get("--max-files", os.getenv("MAX_FILES", 0)))

    supported_file_types = ['.pptx', '.docx', '.pdf', '.jpg', '.jpeg', '.png']

    filter = args.get("--filter", os.getenv("FILTER", None))
    if filter is not None:
        filter = regex.compile(filter)


    file_concurrency = int(args.get("--concurrency", os.getenv('CONCURRENCY', 4)))
    worker_concurrency = int(args.get("--workers", os.getenv('WORKERS', 8)))
    work_executor = ThreadPoolExecutor(max_workers=worker_concurrency)
    total_files = len([file for file in source_path.iterdir() if file.suffix in supported_file_types and (filter is None or filter.search(file.stem))])
    if max_files > 0 and total_files > max_files:
        total_files = max_files

    progress_bar = tqdm(total=total_files, desc="Processing Files", unit="files")
    with ThreadPoolExecutor(max_workers=file_concurrency) as files_executor:
        futures = []
        for file in source_path.iterdir():
            if file.suffix in supported_file_types and (filter is None or filter.search(file.stem)):
                futures.append(files_executor.submit(process_file, file, interim_path, output_path, client, notetaking_model, interpretation_model, work_executor, force_update, progress_bar))
            if max_files > 0 and len(futures) >= max_files:
                break

        report_file = output_path / "report.csv"
        success_count = 0
        failed_count = 0
        with open(report_file, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["File", "Title", "Journal", "FoR Code 1", "FoR  Code 1 Reasoning", "FoR Code 2", "FoR  Code 2 Reasoning", "FoR Code 3", "FoR  Code 3 Reasoning", "FoR Code 4", "FoR  Code 4 Reasoning", "Funding Sources", "Latrobe Affiliated", "Latrobe Affiliations", "Non-Latrobe Affiliations", "Status", "Error"])
            for future in futures:
                try:
                    success, record = future.result()
                    writer.writerow([
                        record.get("file", ""),
                        record.get("title", ""),
                        record.get("journal", ""),
                        record.get("for_code1", {}).get("code", "") + " " + record.get("for_code1", {}).get("category", ""),
                        record.get("for_code1", {}).get("reasoning", ""),
                        record.get("for_code2", {}).get("code", "") + " " + record.get("for_code2", {}).get("category", ""),
                        record.get("for_code2", {}).get("reasoning", ""),
                        record.get("for_code3", {}).get("code", "") + " " + record.get("for_code3", {}).get("category", ""),
                        record.get("for_code3", {}).get("reasoning", ""),
                        record.get("for_code4", {}).get("code", "") + " " + record.get("for_code4", {}).get("category", ""),
                        record.get("for_code4", {}).get("reasoning", ""),
                        record.get("funding_sources", {}).get("sources", ""),
                        record.get("latrobe_affiliated", ""),
                        "; ".join([f"{aff['name']}" for aff in record.get("latrobe_affiliations", [])]),
                        "; ".join([f"{aff['name']}" for aff in record.get("non_latrobe_affiliations", [])]),
                        "SUCCESS" if success else "FAILED",
                        record.get("error", "")
                    ])
                
                except Exception as e:
                    success = False
                    writer.writerow([
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "FAILED",
                        f"{e}"
                    ])
                                          
                if success:
                    success_count += 1
                else:
                    failed_count += 1

            progress_bar.close()
    print(f"All Done [{success_count} Succeeded, {failed_count} Failed]")


def _parse_args() -> dict[str, str]:
    args = sys.argv[1:]
    if len(args) == 0:
        return {}
    res = {}
    for arg in args:
        if arg.startswith("--"):
            arr = arg.split("=")
            key = arr[0]
            value = arr[1] if len(arr) > 1 else True
            res[key] = value
    return res


if __name__ == "__main__":
    args = _parse_args()
    main(args)
