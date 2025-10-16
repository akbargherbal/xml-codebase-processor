import os
import tiktoken
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import mimetypes
from collections import defaultdict

TOKEN_THRESHOLD = 8_000
IGNORE_DIRS = {"node_modules", ".git", ".venv", "__pycache__", ".pytest_cache", "venv"}
IGNORE_FILES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit to avoid memory issues

# Initialize tokenizer once globally for better performance
encoding = tiktoken.get_encoding("cl100k_base")


def setup_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Get token count of top files in a directory"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=os.getcwd(),
        help="Path to the directory to scan (default: current directory)",
    )
    parser.add_argument(
        "--token-threshold",
        type=int,
        default=TOKEN_THRESHOLD,
        help=f"Minimum token count to include in results (default: {TOKEN_THRESHOLD})",
    )
    parser.add_argument(
        "--dir-threshold",
        type=int,
        default=TOKEN_THRESHOLD,
        help=f"Minimum token count for directories to include in results (default: {TOKEN_THRESHOLD})",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Number of worker threads for parallel processing (default: 4)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="token_counts.csv",
        help="Output CSV filename for file results (default: token_counts.csv)",
    )
    parser.add_argument(
        "--dir-output",
        type=str,
        default="directory_token_counts.csv",
        help="Output CSV filename for directory results (default: directory_token_counts.csv)",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all files regardless of token threshold",
    )
    return parser


def is_text_file(file_path):
    """Check if file is likely a text file based on MIME type and extension."""
    try:
        # Check file extension first (faster)
        if file_path.suffix.lower() in IGNORE_FILES:
            return False

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith("text"):
            return True

        # Check for common code file extensions
        code_extensions = {
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
            ".yml",
            ".yaml",
            ".md",
            ".txt",
            ".csv",
            ".sql",
            ".sh",
            ".bat",
            ".ini",
            ".cfg",
            ".conf",
            ".log",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".kt",
            ".swift",
            ".scala",
            ".r",
        }

        return file_path.suffix.lower() in code_extensions
    except Exception:
        return False


def read_file_safely(file_path):
    """Read file with multiple encoding attempts and size checking."""
    try:
        path_obj = Path(file_path)

        # Check file size to avoid memory issues
        if path_obj.stat().st_size > MAX_FILE_SIZE:
            return None

        # Try UTF-8 first (most common)
        try:
            return path_obj.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try other common encodings
            for encoding_name in ["latin-1", "cp1252", "utf-16"]:
                try:
                    return path_obj.read_text(encoding=encoding_name)
                except UnicodeDecodeError:
                    continue

        return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


def get_token_count(text):
    """Calculate token count for given text."""
    if not text:
        return 0
    try:
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception:
        return 0


def collect_files(directory):
    """Collect all relevant files from directory, filtering out ignored directories and binary files."""
    files = []
    directory_path = Path(directory)

    try:
        for file_path in directory_path.rglob("*"):
            # Skip directories
            if not file_path.is_file():
                continue

            # Skip if any parent directory is in ignore list
            if any(part in IGNORE_DIRS for part in file_path.parts):
                continue

            # Skip if file extension suggests binary file
            if not is_text_file(file_path):
                continue

            files.append(file_path)
    except PermissionError as e:
        print(f"Permission denied accessing {directory}: {e}")

    return files


def process_file(file_path):
    """Process a single file and return its token count."""
    text = read_file_safely(file_path)
    if text is None:
        return None

    token_count = get_token_count(text)
    return str(file_path), token_count


def process_files_parallel(files, max_workers=4):
    """Process files in parallel to improve performance."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all files for processing
        future_to_file = {executor.submit(process_file, file): file for file in files}

        # Collect results as they complete
        for future in as_completed(future_to_file):
            result = future.result()
            if result is not None:
                results.append(result)

    return results


def save_results(data, output_file, token_threshold, include_all=False):
    """Save results to CSV file and display summary."""
    if not data:
        print("No files found matching criteria.")
        return []

    # Create DataFrame
    df = pd.DataFrame(data, columns=["FILE_PATH", "TOKEN_COUNT"])

    # Filter by threshold if not including all
    if not include_all:
        df = df[df["TOKEN_COUNT"] > token_threshold]

    # Sort by token count (descending)
    df = df.sort_values(by="TOKEN_COUNT", ascending=False).reset_index(drop=True)

    # Save to CSV
    df.to_csv(output_file, index=False, encoding="utf-8")

    # Display summary
    print(f"\nFile results saved to: {output_file}")
    print(f"Total files processed: {len(data)}")
    print(f"Files above threshold ({token_threshold} tokens): {len(df)}")

    if len(df) > 0:
        print(f"\nTop 10 files by token count:")
        print(df.head(10).to_string(index=False))
        print(f"\nTotal tokens in top files: {df['TOKEN_COUNT'].sum():,}")

    # Return the data for directory calculations
    return data


def calculate_directory_tokens(base_path, file_data):
    """Calculate token counts for each directory based on file data."""
    directory_tokens = defaultdict(int)
    base_path_obj = Path(base_path)

    for file_path, token_count in file_data:
        file_path_obj = Path(file_path)

        # Get all parent directories relative to base path
        try:
            relative_path = file_path_obj.relative_to(base_path_obj)
            current_dir = base_path_obj

            # Add tokens to each parent directory
            for part in relative_path.parts[:-1]:  # Exclude the file itself
                current_dir = current_dir / part
                directory_tokens[str(current_dir)] += token_count

        except ValueError:
            # File is not under base_path, skip
            continue

    return dict(directory_tokens)


def save_directory_results(
    directory_data, output_file, dir_threshold, include_all=False
):
    """Save directory results to CSV file and display summary."""
    if not directory_data:
        print("No directory data found.")
        return

    # Create DataFrame
    df = pd.DataFrame(
        list(directory_data.items()), columns=["DIRECTORY_PATH", "TOKEN_COUNT"]
    )

    # Filter by threshold if not including all
    if not include_all:
        df = df[df["TOKEN_COUNT"] > dir_threshold]

    # Sort by token count (descending)
    df = df.sort_values(by="TOKEN_COUNT", ascending=False).reset_index(drop=True)

    # Save to CSV
    df.to_csv(output_file, index=False, encoding="utf-8")

    # Display summary
    print(f"\nDirectory results saved to: {output_file}")
    print(f"Total directories processed: {len(directory_data)}")
    print(f"Directories above threshold ({dir_threshold} tokens): {len(df)}")

    if len(df) > 0:
        print(f"\nTop 10 directories by token count:")
        print(df.head(10).to_string(index=False))
        print(f"\nTotal tokens in top directories: {df['TOKEN_COUNT'].sum():,}")


def main():
    """Main function to orchestrate the token audit process."""
    parser = setup_parser()
    args = parser.parse_args()

    # Validate input path
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist.")
        return

    print(f"Scanning directory: {args.path}")
    print(f"File token threshold: {args.token_threshold:,}")
    print(f"Directory token threshold: {args.dir_threshold:,}")
    print(f"Max workers: {args.max_workers}")

    # Collect files
    print("Collecting files...")
    files = collect_files(args.path)
    print(f"Found {len(files)} text files to process")

    if not files:
        print("No files found to process.")
        return

    # Process files
    print("Processing files...")
    results = process_files_parallel(files, args.max_workers)

    # Save file results
    file_data = save_results(
        results, args.output, args.token_threshold, args.include_all
    )

    # Calculate and save directory results
    print("Calculating directory token counts...")
    directory_tokens = calculate_directory_tokens(args.path, file_data)
    save_directory_results(
        directory_tokens, args.dir_output, args.dir_threshold, args.include_all
    )


if __name__ == "__main__":
    main()
