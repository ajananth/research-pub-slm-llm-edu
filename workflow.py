#!/usr/bin/env python

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
import sys
import os
import json
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from openai import AzureOpenAI
from markitdown import MarkItDown


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


def parse_file(file: Path) -> str:
    md = MarkItDown()
    result = md.convert(f"{file}")
    return result


def get_metadata(content:str, client: AzureOpenAI, model: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[{ "role": "system", "content": METADATA_PROMPT}, {"role": "user", "content": content}]
    )
    response = completion.choices[0].message.content
    return json.loads(response)

def get_research_code(content:str, client: AzureOpenAI, model: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[{ "role": "system", "content": FOR_CODE_PROMPT}, {"role": "user", "content": content}]
    )
    response = completion.choices[0].message.content
    return json.loads(response)

def get_funding_source(content:str, client: AzureOpenAI, model: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[{ "role": "system", "content": FUNDING_SOURCE_PROMPT}, {"role": "user", "content": content}]
    )
    response = completion.choices[0].message.content
    return json.loads(response)

def get_affiliations(content:str, client: AzureOpenAI, model: str) -> dict:
    completion = client.chat.completions.create(
        model=model,
        messages=[{ "role": "system", "content": AFFILIATIONS_PROMPT}, {"role": "user", "content": content}]
    )
    response = completion.choices[0].message.content
    return json.loads(response)


def process_file(file: Path, interim_path: Path, client: AzureOpenAI, notetaking_model: str, interpretation_model: str, worker_executor:ThreadPoolExecutor = None, force_update:bool = False) -> None:
    ## Step 0: Parse the source file
    print(f"[{file.stem}] Processing")
    interim_file = interim_path / (file.stem + ".md")
    if force_update or not interim_file.exists():
        print(f"[{file.stem}] Parsing source")
        source_md = parse_file(file)
        with open(interim_file, "w") as f:
            f.write(source_md.text_content)

    ## Step 1: Generate Notes
    content = interim_file.read_text()
    chunks = chunk_file_content(content)
    notes_file = interim_path / (file.stem + "_notes.md")
    if force_update or not notes_file.exists():
        print(f"[{file.stem}] Writing Notes")
        notes_content = ""
        with open(notes_file, "w") as f:
            chunk_num = 0
            chunk_futures = []
            for chunk in chunks:
                chunk_futures.append(worker_executor.submit(client.chat.completions.create, model=interpretation_model, messages=[{ "role": "system", "content": NOTETAKING_PROMPT}, {"role": "user", "content": chunk}]))
            for chunk_future in chunk_futures:
                chunk_num += 1
                completion = chunk_future.result()
                response = completion.choices[0].message.content
                f.write(f"# Chunk {chunk_num}\n\n")
                f.write(f"{response}\n\n")
                notes_content += f"# Chunk {chunk_num}\n\n{response}\n\n"
        
    ## Step 2: Determine the Metadata, Research Code, Funding sources, and affiliaitons in the paper
    metadata_file = interim_path / (file.stem + "_metadata.json")
    research_code_file = interim_path / (file.stem + "_research_code.json")
    funding_source_file = interim_path / (file.stem + "_funding_source.json")
    affiliations_file = interim_path / (file.stem + "_affiliations.json")

    if force_update or not metadata_file.exists() or not research_code_file.exists() or not funding_source_file.exists() or not affiliations_file.exists():
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

    ## Step 3: Generate Report
    report_file = interim_path / (file.stem + "_report.md")
    if force_update or not report_file.exists():
        print(f"[{file.stem}] Generating Report")
        analysis_content = f"## Metadata\n\n{json.dumps(metadata, indent=2)}\n\n## Research Code\n\n{json.dumps(research_code, indent=2)}\n\n## Funding Source\n\n{json.dumps(funding_source, indent=2)}\n\n## Affiliations\n\n{json.dumps(affiliations, indent=2)}\n\n"
        with open(report_file, "w") as f:
            completion = client.chat.completions.create(
                model=notetaking_model,
                messages=[
                    { "role": "system", "content": REPORT_PROMPT}, 
                    {"role": "user", "content": analysis_content}
                    ]
            )
            response = completion.choices[0].message.content
            f.write(response)

    ## Step 3: Return Table Info

    
    print(f"[{file.stem}] Done")        



def main(args: dict[str, str]) -> None: 
    
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

    force_update = args.get("--force-update", os.getenv("FORCE_UPDATE", True))
    
    supported_file_types = ['.pptx', '.docx', '.pdf', '.jpg', '.jpeg', '.png']

    file_concurrency = int(args.get("--concurrency", os.getenv('CONCURRENCY', 4)))
    worker_concurrency = int(args.get("--workers", os.getenv('WORKERS', 16)))
    with ThreadPoolExecutor(max_workers=file_concurrency) as files_executor:
        futures = []
        with ThreadPoolExecutor(max_workers=worker_concurrency) as work_executor:
            for file in source_path.iterdir():
                if file.suffix in supported_file_types:
                    futures.append(files_executor.submit(process_file, file, interim_path, client, notetaking_model, interpretation_model, work_executor, force_update))
                if len(futures) >= 2:
                    break

            for future in futures:
                future.result()




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
