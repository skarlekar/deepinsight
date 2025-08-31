#!/usr/bin/env python3
"""
Utility to find text locations in documents based on character positions.
Usage: python location_finder.py <document_path> <source_location>
Example: python location_finder.py doc.txt "char_299_529"
"""

import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def parse_location(source_location: str) -> Optional[Tuple[int, int]]:
    """Parse source location string like 'char_299_529' into start and end positions."""
    if not source_location or not source_location.startswith('char_'):
        return None
    
    try:
        # Remove 'char_' prefix and split by '_'
        parts = source_location[5:].split('_')
        if len(parts) == 2:
            start = int(parts[0])
            end = int(parts[1])
            return start, end
        return None
    except (ValueError, IndexError):
        return None

def find_text_at_location(document_path: str, source_location: str, context_chars: int = 100) -> dict:
    """Find and return text at the specified character location with context."""
    
    if not os.path.exists(document_path):
        return {"error": f"Document not found: {document_path}"}
    
    location = parse_location(source_location)
    if not location:
        return {"error": f"Invalid source location format: {source_location}"}
    
    start_pos, end_pos = location
    
    try:
        with open(document_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        if start_pos < 0 or end_pos > len(content) or start_pos >= end_pos:
            return {"error": f"Invalid character positions: {start_pos}-{end_pos} for document length {len(content)}"}
        
        # Extract the exact text
        exact_text = content[start_pos:end_pos]
        
        # Get context before and after
        context_start = max(0, start_pos - context_chars)
        context_end = min(len(content), end_pos + context_chars)
        context_text = content[context_start:context_end]
        
        # Calculate line numbers
        lines_before = content[:start_pos].count('\n')
        start_line = lines_before + 1
        
        lines_in_text = exact_text.count('\n')
        end_line = start_line + lines_in_text
        
        # Get character position within the line
        last_newline = content.rfind('\n', 0, start_pos)
        char_in_line = start_pos - (last_newline + 1) if last_newline != -1 else start_pos
        
        return {
            "document": document_path,
            "source_location": source_location,
            "character_range": f"{start_pos}-{end_pos}",
            "line_range": f"{start_line}-{end_line}",
            "char_in_line": char_in_line + 1,  # 1-indexed for user readability
            "exact_text": exact_text,
            "context_text": context_text,
            "context_markers": {
                "before_chars": start_pos - context_start,
                "after_chars": context_end - end_pos
            }
        }
        
    except Exception as e:
        return {"error": f"Error reading document: {str(e)}"}

def display_result(result: dict):
    """Display the location result in a readable format."""
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print("📍 Location Found:")
    print(f"   Document: {result['document']}")
    print(f"   Characters: {result['character_range']}")
    print(f"   Lines: {result['line_range']}")
    print(f"   Position in line: {result['char_in_line']}")
    print()
    print("📝 Extracted Text:")
    print(f'   "{result["exact_text"]}"')
    print()
    print("🔍 Context (with surrounding text):")
    before_chars = result['context_markers']['before_chars']
    after_chars = result['context_markers']['after_chars']
    context = result['context_text']
    
    # Highlight the extracted portion
    highlighted_context = (
        context[:before_chars] + 
        ">>>" + context[before_chars:len(context)-after_chars] + "<<<" +
        context[len(context)-after_chars:]
    )
    print(f'   "{highlighted_context}"')

def main():
    if len(sys.argv) != 3:
        print("Usage: python location_finder.py <document_path> <source_location>")
        print("Example: python location_finder.py document.txt 'char_299_529'")
        sys.exit(1)
    
    document_path = sys.argv[1]
    source_location = sys.argv[2]
    
    result = find_text_at_location(document_path, source_location)
    display_result(result)

if __name__ == "__main__":
    main()