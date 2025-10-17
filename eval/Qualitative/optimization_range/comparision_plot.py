import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import mannwhitneyu

# =====================================================
# Load datasets
# =====================================================

# --- With catalog ---
biojava_with = pd.DataFrame({
    "file_name": [
        "AbstractSequence.java", "AminoAcidCompound.java", "AminoAcidCompoundSet.java",
        "CommandPrompt.java", "FastaReader.java", "GenericFastaHeaderParser.java",
        "PeptidePropertiesImpl.java", "ProteinSequence.java", "SequenceMixin.java",
        "Utils.java"
    ],
    "functions_compared": [68, 7, 17, 10, 5, 4, 36, 8, 25, 7],
    "functions_changed": [8, 6, 11, 6, 2, 4, 17, 4, 15, 6]
})
biojava_with["app"] = "Biojava"

pmd_with = pd.DataFrame({
    "file_name": ["AbstractNode.java", "AbstractRule.java", "AttributeAxisIterator.java",
                  "ElementNode.java", "IOUtil.java", "RuleSetFactory.java",
                  "RuleSetFactoryCompatibility.java", "SaxonXPathRuleQuery.java", "XPathRule.java"],
    "functions_compared": [64, 63, 11, 21, 40, 30, 21, 16, 14],
    "functions_changed": [11, 8, 3, 3, 5, 8, 16, 4, 2]
})
pmd_with["app"] = "Pmd"

graphchi_with = pd.DataFrame({
    "file_name": ["ChiPointer.java", "ChiVertex.java", "DataBlockManager.java", "FloatConverter.java"],
    "functions_compared": [4, 24, 10, 3],
    "functions_changed": [3, 11, 6, 2]
})
graphchi_with["app"] = "Graphchi"

fop_with = pd.DataFrame({
    "file_name": [
        "CondLengthProperty.java", "DelegatingContentHandler.java", "ElementListUtils.java",
        "FOElementMapping.java", "FOEventHandler.java", "FOText.java", "FObj.java",
        "FlowLayoutManager.java", "FopFactoryBuilder.java", "InputHandler.java",
        "LayoutManagerMapping.java", "Main.java", "NCnameProperty.java", "PDFMetadata.java",
        "PDFNumber.java", "PDFStream.java", "RendererFactory.java", "UnicodeBidiAlgorithm.java"
    ],
    "functions_compared": [16, 37, 13, 68, 75, 57, 66, 22, 99, 15, 62, 8, 7, 8, 10, 19, 23, 34],
    "functions_changed": [7, 24, 2, 65, 1, 10, 13, 6, 3, 8, 54, 6, 1, 2, 4, 6, 15, 6]
})
fop_with["app"] = "Fop"

zxing_with = pd.DataFrame({
    "file_name": [
        "BitArray.java", "BitMatrix.java", "Code39Reader.java", "Code93Reader.java",
        "Detector.java", "GlobalHistogramBinarizer.java", "HybridBinarizer.java", "OneDReader.java"
    ],
    "functions_compared": [27, 31, 17, 17, 13, 6, 7, 7],
    "functions_changed": [13, 9, 16, 17, 10, 1, 4, 3]
})
zxing_with["app"] = "Zxing"

with_catalog = pd.concat([biojava_with, pmd_with, graphchi_with, fop_with, zxing_with], ignore_index=True)


# --- Without catalog ---
biojava_no = pd.DataFrame({
    "file_name": [
        "AbstractSequence.java", "AminoAcidCompound.java", "AminoAcidCompoundSet.java",
        "CommandPrompt.java", "FastaReader.java", "PeptidePropertiesImpl.java",
        "SequenceMixin.java", "Utils.java"
    ],
    "functions_compared": [73, 5, 17, 9, 5, 34, 25, 8],
    "functions_changed": [19, 4, 10, 4, 1, 13, 7, 7]
})
biojava_no["app"] = "Biojava"

fop_no = pd.DataFrame({
    "file_name": [
        "AbstractPDFStream.java", "FOElementMapping.java", "FOUserAgent.java",
        "FopFactoryBuilder.java", "ImageHandlerRegistry.java", "InputHandler.java",
        "LayoutManagerMapping.java", "Main.java", "PDFDocumentHandler.java",
        "PDFNumber.java", "PDFStream.java", "PageSequenceLayoutManager.java",
        "Property.java", "RendererFactory.java"
    ],
    "functions_compared": [20, 68, 80, 100, 11, 14, 37, 9, 32, 9, 16, 38, 19, 23],
    "functions_changed": [6, 1, 6, 67, 10, 7, 7, 7, 4, 4, 4, 5, 1, 15]
})
fop_no["app"] = "Fop"

zxing_no = pd.DataFrame({
    "file_name": [
        "BitArray.java", "BitMatrix.java", "Code128Reader.java",
        "Code39Reader.java", "Code93Reader.java", "Detector.java",
        "GlobalHistogramBinarizer.java", "HybridBinarizer.java", "OneDReader.java"
    ],
    "functions_compared": [27, 31, 3, 17, 19, 9, 6, 7, 7],
    "functions_changed": [0, 12, 2, 16, 18, 2, 3, 3, 3]
})
zxing_no["app"] = "Zxing"

pmd_no = pd.DataFrame({
    "file_name": [
        "AbstractNode.java", "AbstractRule.java", "AbstractRuleViolationFactory.java",
        "Attribute.java", "AttributeAxisIterator.java", "ElementNode.java", "IOUtil.java",
        "RuleSetFactory.java", "RuleSetFactoryCompatibility.java", "SaxonXPathRuleQuery.java",
        "XPathRule.java"
    ],
    "functions_compared": [64, 62, 3, 11, 12, 22, 41, 34, 15, 16, 15],
    "functions_changed": [11, 12, 1, 4, 8, 5, 6, 17, 1, 6, 6]
})
pmd_no["app"] = "Pmd"

graphchi_no = pd.DataFrame({
    "file_name": ["ChiPointer.java", "ChiVertex.java", "DataBlockManager.java", "FloatConverter.java"],
    "functions_compared": [4, 27, 9, 3],
    "functions_changed": [3, 12, 6, 2]
})
graphchi_no["app"] = "Graphchi"

without_catalog = pd.concat([biojava_no, pmd_no, graphchi_no, fop_no, zxing_no], ignore_index=True)

# =====================================================
# Comparison & Visualization
# =====================================================

# Add fraction changed + condition labels
with_catalog["frac_changed"] = with_catalog["functions_changed"] / with_catalog["functions_compared"]
with_catalog["condition"] = "With Catalog"

without_catalog["frac_changed"] = without_catalog["functions_changed"] / without_catalog["functions_compared"]
without_catalog["condition"] = "Without Catalog"

combined = pd.concat([with_catalog, without_catalog], ignore_index=True)

# --- 1. Files touched (bar chart) ---
files_touched = (
    combined.groupby(["app", "condition"])["file_name"]
    .nunique()
    .reset_index(name="files_touched")
)

plt.figure(figsize=(8,5))
sns.barplot(data=files_touched, x="app", y="files_touched", hue="condition")
plt.ylabel("Number of Files Touched")
plt.title("Files Touched per App (With vs Without Catalog)")
plt.tight_layout()
plt.savefig("files_touched_comparison.png", dpi=200)
plt.show()

# --- 2. Fraction changed (boxplots) ---
plt.figure(figsize=(8,5))
sns.boxplot(
    data=combined,
    x="app", y="frac_changed", hue="condition",
    showfliers=True,
    whis=[10, 90]
)
plt.ylabel("Fraction of Functions Changed per Class")
plt.title("Distribution of Fraction of Functions Changed: With and Without Catalog")
plt.tight_layout()
plt.savefig("frac_changed_comparison.png", dpi=200)
plt.show()

# --- 3. Summary table ---
summary = combined.groupby(["app", "condition"]).agg(
    files_touched=("file_name", "nunique"),
    median_changed=("functions_changed", "median"),
    mean_changed=("functions_changed", "mean"),
    median_frac_changed=("frac_changed", "median"),
    mean_frac_changed=("frac_changed", "mean"),
    total_changed=("functions_changed", "sum")
)
summary.to_csv("functions_changed_comparison.csv")
print(summary)

# --- 4. Optional: Mann–Whitney U test ---
print("\nMann–Whitney U Test on fraction changed per app:")
apps = combined["app"].unique()
for app in apps:
    data_with = combined[(combined["app"] == app) & (combined["condition"] == "With Catalog")]["frac_changed"]
    data_without = combined[(combined["app"] == app) & (combined["condition"] == "Without Catalog")]["frac_changed"]
    if len(data_with) > 0 and len(data_without) > 0:
        stat, p = mannwhitneyu(data_with, data_without, alternative="two-sided")
        print(f"{app}: U={stat}, p-value={p:.4f}")
