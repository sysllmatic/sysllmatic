#!/usr/bin/env python3
"""
Extract rows from a JaCoCo CSV report based on a hard-coded list of class names.

Usage:
    python extract_jacoco_rows_by_class.py jacoco.csv output.csv
"""

import csv
import sys

# =========================
# CONFIG: target classes
# =========================
TARGET_CLASSES_BIOJAVA = {
    "AbstractSequence",
    "AminoAcidCompound",
    "AminoAcidCompoundSet",
    "CommandPrompt",
    "FastaReader",
    "GenericFastaHeaderParser",
    "PeptidePropertiesImpl",
    "ProteinSequence",
    "SequenceMixin",
    "Utils",
}

TARGET_CLASSES_FOP = {
    "CondLengthProperty",
    "DelegatingContentHandler",
    "ElementListUtils",
    "FlowLayoutManager",
    "FObj",
    "FOElementMapping",
    "FOEventHandler",
    "FopFactoryBuilder",
    "FOText",
    "InputHandler",
    "LayoutManagerMapping",
    "Main",
    "NCnameProperty",
    "PDFMetadata",
    "PDFNumber",
    "PDFStream",
    "RendererFactory",
    "UnicodeBidiAlgorithm",
}

TARGET_CLASSES_PMD = {
    "AbstractNode",
    "AbstractRule",
    "AttributeAxisIterator",
    "ElementNode",
    "IOUtil",
    "RuleSetFactory",
    "RuleSetFactoryCompatibility",
    "SaxonXPathRuleQuery",
    "XPathRule",
}

TARGET_CLASSES_ZXING = {
    "BitArray",
    "BitMatrix",
    "Code39Reader",
    "Code93Reader",
    "Detector",
    "GlobalHistogramBinarizer",
    "HybridBinarizer",
    "OneDReader",
}

TARGET_CLASSES = {
    "ChiPointer",
    "ChiVertex",
    "DataBlockManager",
    "FloatConverter",
}

def extract_rows(input_csv, output_csv):
    with open(input_csv, newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        matched_rows = [
            row for row in reader
            if row.get("CLASS") in TARGET_CLASSES
        ]

    if not matched_rows:
        print("Warning: no matching classes found.", file=sys.stderr)

    with open(output_csv, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matched_rows)

    print(f"Extracted {len(matched_rows)} rows to {output_csv}")

def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python extract_coverage_rows.py <jacoco.csv> <output.csv>",
            file=sys.stderr,
        )
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2]

    extract_rows(input_csv, output_csv)

if __name__ == "__main__":
    main()