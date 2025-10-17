import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product
import numpy as np

# -----------------------------
# 1. Raw data (replace with your actual full lists)
# -----------------------------
cpu = [('org/biojava/nbio/core/sequence/template/SequenceMixin.toStringBuilder', 376), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.getCompoundForString', 203), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.setContents', 83), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getMolecularWeight', 55), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getInstabilityIndex', 48), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAAComposition', 45), ('org/biojava/nbio/aaproperties/xml/CaseFreeAminoAcidCompoundSet.getCompoundForString', 34), ('org/biojava/nbio/core/sequence/io/FastaReader.<clinit>', 31), ('org/biojava/nbio/aaproperties/Utils.cleanSequence', 31), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAvgHydropathy', 28), ('org/biojava/nbio/aaproperties/Utils.getNumberOfInvalidChar', 25), ('org/biojava/nbio/aaproperties/CommandPrompt.compute', 19), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getSequence', 18), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getExtinctAACount', 17), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.hashCode', 14), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.<init>', 14), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPointExpasy', 11), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getNetChargeExpasy', 11), ('org/biojava/nbio/core/sequence/io/BufferedReaderBytesRead.readLine', 6), ('org/biojava/nbio/core/sequence/template/AbstractCompound.toString', 5), ('org/biojava/nbio/core/sequence/template/AbstractSequence.getSequenceStorage', 2), ('org/biojava/nbio/core/sequence/io/GenericFastaHeaderParser.getHeaderValues', 2), ('org/biojava/nbio/core/sequence/template/SequenceMixin.toString', 2), ('org/biojava/nbio/aaproperties/CommandPrompt.readInputAndGenerateOutput', 2), ('org/biojava/nbio/core/sequence/template/AbstractCompound.<init>', 2), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getNetCharge', 2), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.equals', 2), ('org/biojava/nbio/core/sequence/io/BufferedReaderBytesRead.fill', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPoint', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.exp10', 1), ('org/biojava/nbio/core/sequence/io/FastaReader.process', 1), ('org/biojava/nbio/aaproperties/Utils.doesSequenceContainInvalidChar', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.<init>', 1)]

alloc = [('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getMolecularWeight', 5832), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.setContents', 4377), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAvgHydropathy', 2023), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getInstabilityIndex', 1926), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAAComposition', 1253), ('org/biojava/nbio/core/sequence/template/SequenceMixin.toString', 605), ('org/biojava/nbio/core/sequence/template/SequenceMixin.toStringBuilder', 599), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getSequence', 488), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.<init>', 397), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getExtinctAACount', 342), ('org/biojava/nbio/aaproperties/Utils.cleanSequence', 228), ('org/biojava/nbio/core/sequence/io/BufferedReaderBytesRead.readLine', 109), ('org.biojava.nbio.core.sequence.compound.AminoAcidCompound_[i]', 98), ('org/biojava/nbio/aaproperties/Utils.doesSequenceContainInvalidChar', 82), ('org/biojava/nbio/aaproperties/Utils.getNumberOfInvalidChar', 81), ('org/biojava/nbio/core/sequence/io/FastaReader.<clinit>', 45), ('org/biojava/nbio/core/sequence/io/FastaReader.process', 41), ('org/biojava/nbio/aaproperties/CommandPrompt.compute', 26), ('org/biojava/nbio/core/sequence/io/GenericFastaHeaderParser.getHeaderValues', 11), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.<init>', 8), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.getAllCompounds', 5), ('org.biojava.nbio.core.sequence.compound.AminoAcidCompoundSet_[i]', 5), ('org.biojava.nbio.core.sequence.ProteinSequence_[i]', 4), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPointExpasy', 3), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.iterator', 2), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.<init>', 1), ('org.biojava.nbio.core.sequence.AccessionID_[i]', 1), ('org/biojava/nbio/core/sequence/template/AbstractSequence.<init>', 1)]

wall = [('org/biojava/nbio/core/sequence/template/SequenceMixin.toStringBuilder', 66), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.getCompoundForString', 41), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getMolecularWeight', 18), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.setContents', 14), ('org/biojava/nbio/aaproperties/Utils.cleanSequence', 10), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getInstabilityIndex', 10), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAAComposition', 6), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getExtinctAACount', 6), ('org/biojava/nbio/aaproperties/xml/CaseFreeAminoAcidCompoundSet.getCompoundForString', 6), ('org/biojava/nbio/core/sequence/io/FastaReader.<clinit>', 5), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAvgHydropathy', 5), ('org/biojava/nbio/aaproperties/Utils.getNumberOfInvalidChar', 5), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.<init>', 5), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.hashCode', 4), ('org/biojava/nbio/aaproperties/CommandPrompt.compute', 3), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPointExpasy', 3), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.equals', 1), ('org/biojava/nbio/aaproperties/Utils.doesSequenceContainInvalidChar', 1), ('org/biojava/nbio/core/sequence/template/AbstractSequence.getSequenceStorage', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getNetChargeExpasy', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getSequence', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.exp10', 1), ('org/biojava/nbio/core/sequence/io/GenericFastaHeaderParser.getHeaderValues', 1), ('org/biojava/nbio/core/sequence/io/FastaReader.process', 1)]

itimer = [('org/biojava/nbio/core/sequence/template/SequenceMixin.toStringBuilder', 347), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.getCompoundForString', 228), ('org/biojava/nbio/core/sequence/storage/ArrayListSequenceReader.setContents', 106), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getMolecularWeight', 70), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getInstabilityIndex', 69), ('org/biojava/nbio/aaproperties/Utils.cleanSequence', 45), ('org/biojava/nbio/core/sequence/io/FastaReader.<clinit>', 41), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAAComposition', 39), ('org/biojava/nbio/aaproperties/Utils.getNumberOfInvalidChar', 24), ('org/biojava/nbio/aaproperties/xml/CaseFreeAminoAcidCompoundSet.getCompoundForString', 24), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getAvgHydropathy', 20), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompoundSet.<init>', 19), ('org/biojava/nbio/aaproperties/CommandPrompt.compute', 19), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getExtinctAACount', 18), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.hashCode', 15), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPointExpasy', 10), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getSequence', 9), ('org/biojava/nbio/core/sequence/template/AbstractCompound.toString', 8), ('org/biojava/nbio/core/sequence/io/BufferedReaderBytesRead.readLine', 6), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getNetChargeExpasy', 4), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getNetCharge', 4), ('org/biojava/nbio/core/sequence/io/BufferedReaderBytesRead.fill', 3), ('org/biojava/nbio/core/sequence/template/AbstractCompound.<init>', 3), ('org/biojava/nbio/core/sequence/compound/AminoAcidCompound.equals', 3), ('org/biojava/nbio/core/sequence/template/AbstractSequence.getSequenceStorage', 2), ('org/biojava/nbio/aaproperties/Utils.doesSequenceContainInvalidChar', 2), ('org/biojava/nbio/core/sequence/template/SequenceMixin.toString', 2), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getIsoelectricPoint', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.exp10', 1), ('org/biojava/nbio/aaproperties/Utils.get$Lambda', 1), ('org/biojava/nbio/aaproperties/CommandPrompt.readInputFile', 1), ('org/biojava/nbio/aaproperties/PeptidePropertiesImpl.getWaterMoleculeWeight', 1), ('org/biojava/nbio/aaproperties/Constraints.initInstability', 1), ('org/biojava/nbio/aaproperties/Utils.roundToDecimals', 1)]

datasets = {"cpu": cpu, "alloc": alloc, "wall": wall, "itimer": itimer}

# -----------------------------
# 2. Normalize counts into percentages
# -----------------------------
dfs = []
for name, data in datasets.items():
    df = pd.DataFrame(data, columns=["method", name])
    total = df[name].sum()
    df[name] = df[name] / total * 100.0   # normalize to percentage
    dfs.append(df)

# -----------------------------
# 3. Merge into one table
# -----------------------------
merged = dfs[0]
for df in dfs[1:]:
    merged = pd.merge(merged, df, on="method", how="outer")
merged = merged.fillna(0)

# -----------------------------
# 4. Compute correlations
# -----------------------------
corr = merged.drop(columns=["method"]).corr()

plt.figure(figsize=(7, 5))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation Between Profiling Metrics - Biojava")
plt.show()
plt.savefig("heatmap.png", bbox_inches="tight")

# -----------------------------
# 6. Save merged table for inspection
# -----------------------------
merged.to_csv("profiling_summary.csv", index=False)
print("Merged profiling data saved to profiling_summary.csv")

# 1. Build sets of methods per event
method_sets = {name: set(df["method"]) for name, df in zip(datasets.keys(), dfs)}

# 2. Compute Jaccard similarity matrix
events = list(method_sets.keys())
jac = pd.DataFrame(index=events, columns=events, dtype=float)

for a, b in product(events, events):
    inter = len(method_sets[a] & method_sets[b])
    union = len(method_sets[a] | method_sets[b])
    jac.loc[a, b] = inter / union if union > 0 else 0.0

# 3. Plot heatmap
plt.figure(figsize=(7, 5))
sns.heatmap(jac, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Jaccard Similarity Between Profiling Hotspots - Biojava")
plt.show()
plt.savefig("Jaccard.png", bbox_inches="tight")
