import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product
import numpy as np

# -----------------------------
# 1. Raw data (replace with your actual full lists)
# -----------------------------
cpu = [('edu/cmu/graphchi/apps/ALSMatrixFactorization.update', 6769), ('edu/cmu/graphchi/util/HugeDoubleMatrix.getRow', 55), ('edu/cmu/graphchi/util/HugeDoubleMatrix.setValue', 46), ('edu/cmu/graphchi/shards/MemoryShard.loadAdjChunk', 27), ('edu/cmu/graphchi/util/HugeDoubleMatrix.randomize', 27), ('edu/cmu/graphchi/ChiVertex.numEdges', 23), ('edu/cmu/graphchi/io/CompressedIO.readCompressed', 13), ('edu/cmu/graphchi/engine/GraphChiEngine.run', 12), ('edu/cmu/graphchi/shards/SlidingShard.readNextVertices', 11), ('edu/cmu/graphchi/ChiVertex.addOutEdge', 11), ('edu/cmu/graphchi/ChiVertex.outEdge', 11), ('edu/cmu/graphchi/ChiVertex.<init>', 11), ('edu/cmu/graphchi/datablocks/DataBlockManager.getRawBlock', 9), ('edu/cmu/graphchi/engine/GraphChiEngine.<init>', 7), ('edu/cmu/graphchi/engine/GraphChiEngine.initVertices', 6), ('edu/cmu/graphchi/ChiVertex.edge', 5), ('edu/cmu/graphchi/ChiVertex.inEdge', 4), ('edu/cmu/graphchi/util/HugeDoubleMatrix.<init>', 4), ('edu/cmu/graphchi/ChiVertex.addInEdge', 4), ('edu/cmu/graphchi/engine/auxdata/DegreeData.getDegree', 3), ('edu/cmu/graphchi/shards/MemoryShard.loadAdj', 3), ('edu/cmu/graphchi/engine/GraphChiEngine.execUpdates', 3), ('edu/cmu/graphchi/datablocks/ChiPointer.<init>', 3), ('edu/cmu/graphchi/datablocks/FloatConverter.getValue', 2), ('edu/cmu/graphchi/engine/GraphChiEngine.determineNextWindow', 2), ('edu/cmu/graphchi/datablocks/DataBlockManager.allocateBlock', 1), ('edu/cmu/graphchi/shards/SlidingShard.checkCurblock', 1), ('edu/cmu/graphchi/engine/GraphChiEngine.loadBeforeUpdates', 1), ('edu/cmu/graphchi/engine/auxdata/DegreeData.load', 1), ('edu/cmu/graphchi/ChiVertex.getId', 1), ('edu/cmu/graphchi/shards/SlidingShard.readEdgePtr', 1)]

alloc = [('edu/cmu/graphchi/apps/ALSMatrixFactorization.update', 19805), ('edu.cmu.graphchi.datablocks.ChiPointer_[i]', 597), ('edu.cmu.graphchi.ChiVertex$Edge_[i]', 538), ('edu/cmu/graphchi/ChiVertex.<init>', 319), ('edu.cmu.graphchi.ChiVertex_[i]', 101), ('edu/cmu/graphchi/shards/MemoryShard.loadAdj', 31), ('edu.cmu.graphchi.engine.auxdata.VertexDegree_[i]', 20), ('edu/cmu/graphchi/datablocks/DataBlockManager.allocateBlock', 19), ('edu/cmu/graphchi/shards/SlidingShard.readNextVertices', 11), ('edu/cmu/graphchi/engine/auxdata/DegreeData.load', 10), ('edu.cmu.graphchi.ChiVertex[]_[i]', 9), ('edu.cmu.graphchi.GraphChiContext_[i]', 6), ('edu/cmu/graphchi/engine/GraphChiEngine.<init>', 5), ('edu/cmu/graphchi/engine/GraphChiEngine.execUpdates', 5), ('edu/cmu/graphchi/datablocks/FloatConverter.getValue', 4), ('edu/cmu/graphchi/engine/auxdata/DegreeData.getDegree', 2), ('edu/cmu/graphchi/apps/ALSMatrixFactorization.createSharder', 1), ('edu/cmu/graphchi/shards/MemoryShard.loadAdjChunk', 1), ('edu/cmu/graphchi/util/HugeDoubleMatrix.<init>', 1), ('edu/cmu/graphchi/engine/GraphChiEngine.run', 1), ('edu/cmu/graphchi/engine/GraphChiEngine.determineNextWindow', 1), ('edu/cmu/graphchi/shards/ShardIndex.sparserIndex', 1), ('edu/cmu/graphchi/shards/ShardIndex.load', 1)]

lock = [('edu/cmu/graphchi/apps/ALSMatrixFactorization.update', 214), ('edu/cmu/graphchi/ChiVertex.outEdge', 7), ('edu/cmu/graphchi/datablocks/FloatConverter.getValue', 6), ('edu/cmu/graphchi/engine/GraphChiEngine.run', 2)]

wall = [('edu/cmu/graphchi/apps/ALSMatrixFactorization.update', 1234), ('edu/cmu/graphchi/engine/GraphChiEngine.execUpdates', 107), ('edu/cmu/graphchi/util/HugeDoubleMatrix.setValue', 11), ('edu/cmu/graphchi/util/HugeDoubleMatrix.getRow', 9), ('edu/cmu/graphchi/shards/MemoryShard.loadVertices', 8), ('edu/cmu/graphchi/shards/MemoryShard.loadAdjChunk', 6), ('edu/cmu/graphchi/util/HugeDoubleMatrix.randomize', 6), ('edu/cmu/graphchi/engine/GraphChiEngine.loadBeforeUpdates', 5), ('edu/cmu/graphchi/io/CompressedIO.readCompressed', 4), ('edu/cmu/graphchi/ChiVertex.addInEdge', 4), ('edu/cmu/graphchi/engine/GraphChiEngine.initVertices', 3), ('edu/cmu/graphchi/engine/GraphChiEngine.run', 2), ('edu/cmu/graphchi/shards/SlidingShard.readNextVertices', 2), ('edu/cmu/graphchi/engine/GraphChiEngine.<init>', 2), ('edu/cmu/graphchi/ChiVertex.outEdge', 1), ('edu/cmu/graphchi/datablocks/DataBlockManager.dereference', 1), ('edu/cmu/graphchi/ChiVertex.addOutEdge', 1), ('edu/cmu/graphchi/ChiVertex.edge', 1), ('edu/cmu/graphchi/ChiVertex.numEdges', 1), ('edu/cmu/graphchi/shards/MemoryShard.loadAdj', 1), ('edu/cmu/graphchi/ChiVertex.<init>', 1), ('edu/cmu/graphchi/util/HugeDoubleMatrix.<init>', 1), ('edu/cmu/graphchi/ChiVertex.inEdge', 1)]

itimer = [('edu/cmu/graphchi/apps/ALSMatrixFactorization.update', 1173), ('edu/cmu/graphchi/shards/MemoryShard.loadAdjChunk', 37), ('edu/cmu/graphchi/util/HugeDoubleMatrix.getRow', 29), ('edu/cmu/graphchi/util/HugeDoubleMatrix.randomize', 29), ('edu/cmu/graphchi/shards/SlidingShard.readNextVertices', 19), ('edu/cmu/graphchi/io/CompressedIO.readCompressed', 17), ('edu/cmu/graphchi/ChiVertex.addOutEdge', 10), ('edu/cmu/graphchi/util/HugeDoubleMatrix.setValue', 10), ('edu/cmu/graphchi/engine/GraphChiEngine.initVertices', 8), ('edu/cmu/graphchi/datablocks/FloatConverter.getValue', 7), ('edu/cmu/graphchi/engine/GraphChiEngine.<init>', 7), ('edu/cmu/graphchi/engine/auxdata/DegreeData.getDegree', 6), ('edu/cmu/graphchi/ChiVertex.addInEdge', 6), ('edu/cmu/graphchi/util/HugeDoubleMatrix.<init>', 6), ('edu/cmu/graphchi/ChiVertex.inEdge', 3), ('edu/cmu/graphchi/ChiVertex.<init>', 3), ('edu/cmu/graphchi/engine/GraphChiEngine.determineNextWindow', 2), ('edu/cmu/graphchi/engine/GraphChiEngine.execUpdates', 2), ('edu/cmu/graphchi/ChiVertex.getUnsafe', 1), ('edu/cmu/graphchi/shards/MemoryShard.loadAdj', 1), ('edu/cmu/graphchi/engine/GraphChiEngine.run', 1), ('edu/cmu/graphchi/ChiVertex.numInEdges', 1), ('edu/cmu/graphchi/datablocks/DataBlockManager.dereference', 1), ('edu/cmu/graphchi/shards/MemoryShard.loadVertices', 1), ('edu/cmu/graphchi/apps/ALSMatrixFactorization.<clinit>', 1), ('edu/cmu/graphchi/ChiVertex.outEdge', 1)]

datasets = {"cpu": cpu, "alloc": alloc, "lock": lock, "wall": wall, "itimer": itimer}

# -----------------------------
# 2. Normalize counts into percentages
# -----------------------------
dfs = []
for name, data in datasets.items():
    df = pd.DataFrame(data, columns=["method", name])
    # total = df[name].sum()
    # df[name] = df[name] / total * 100.0   # normalize to percentage
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
plt.title("Correlation Between Profiling Metrics - Graphchi")
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
plt.title("Jaccard Similarity Between Profiling Hotspots - Graphchi")
plt.show()
plt.savefig("Jaccard.png", bbox_inches="tight")

