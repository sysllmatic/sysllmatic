import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import product
import numpy as np

# -----------------------------
# 1. Raw data (replace with your actual full lists)
# -----------------------------
cpu = [('org/apache/fop/render/pdf/PDFImageHandlerSVG.handleImage', 13), ('org/apache/fop/cli/InputHandler.transformTo', 13), ('org/apache/fop/image/loader/batik/PreloaderSVG.createImageInfo', 11), ('org/apache/fop/render/intermediate/IFRenderer.createDefaultDocumentMetadata', 6), ('org/apache/fop/apps/FopFactoryBuilder.<init>', 5), ('org/apache/fop/cli/InputHandler.getXMLReader', 4), ('org/apache/fop/pdf/PDFMetadata.outputRawStreamData', 4), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.initWord', 3), ('org/apache/fop/fo/extensions/svg/BatikExtensionElementMapping.getAParserClassName', 3), ('org/apache/fop/image/loader/batik/PreloaderWMF.preloadImage', 3), ('org/apache/fop/fo/extensions/svg/SVGElementMapping.getAParserClassName', 3), ('org/apache/fop/pdf/PDFStream.streamHashCode', 3), ('org/apache/fop/svg/PDFBridgeContext.registerSVGBridges', 3), ('org/apache/fop/image/loader/batik/BatikUtil.isBatikAvailable', 3), ('org/apache/fop/util/text/GlyphNameFieldPart.getGlyphName', 2), ('org/apache/fop/image/loader/batik/BatikUtil.cloneSVGDocument', 2), ('org/apache/fop/hyphenation/Hyphenator.getResourceStream', 2), ('org/apache/fop/fo/expr/PropertyParser.parsePrimaryExpr', 2), ('org/apache/fop/layoutmgr/BreakingAlgorithm.computeDemerits', 2), ('org/apache/fop/pdf/PDFNumber.doubleOut', 2), ('org/apache/fop/layoutmgr/FloatContentLayoutManager.checkForFloats', 2), ('org/apache/fop/fo/ElementMappingRegistry.addElementMapping', 2), ('org/apache/fop/fo/StaticPropertyList.<init>', 2), ('org/apache/fop/cli/CommandLineOptions.<init>', 2), ('org/apache/fop/layoutmgr/BreakingAlgorithm.forceNode', 2), ('org/apache/fop/layoutmgr/BreakingAlgorithm.considerLegalBreak', 2), ('org/apache/fop/render/intermediate/AbstractIFPainter.drawImageUsingImageHandler', 2), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.getNextKnuthElements', 2), ('org/apache/fop/render/ImageHandlerRegistry.addHandler', 2), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.makeZeroWidthPenalty', 2), ('org/apache/fop/fo/extensions/svg/SVGDOMContentHandlerFactory.startElement', 2), ('org/apache/fop/svg/PDFGraphics2D.<init>', 2), ('org/apache/fop/fo/properties/CompoundPropertyMaker.makeCompound', 2), ('org/apache/fop/pdf/PDFColorHandler.writeColor', 2), ('org/apache/fop/render/pdf/PDFDocumentHandler.<init>', 1), ('org/apache/fop/image/loader/batik/PreloaderSVG.getImage', 1), ('org/apache/fop/render/pdf/PDFRenderingUtil.setupPDFDocument', 1), ('org/apache/fop/fonts/Font.hasCodePoint', 1), ('org/apache/fop/events/model/EventModelParser.parse', 1), ('org/apache/fop/render/PrintRenderer.getInternalFontNameForArea', 1), ('org/apache/fop/fonts/FontInfo.getFontInstance', 1), ('org/apache/fop/render/AbstractRenderer.renderBlock', 1), ('org/apache/fop/fo/FONode.collectDelimitedTextRanges', 1), ('org/apache/fop/layoutmgr/table/TableCellLayoutManager.getNextKnuthElements', 1), ('org/apache/fop/fo/RecursiveCharIterator.getNextCharIter', 1), ('org/apache/fop/layoutmgr/inline/LineLayoutManager.collectInlineKnuthElements', 1), ('org/apache/fop/layoutmgr/table/RowGroupLayoutManager.computeRowHeights', 1), ('org/apache/fop/render/intermediate/IFGraphicContext.<init>', 1), ('org/apache/fop/area/Area.addTrait', 1), ('org/apache/fop/render/pdf/CTMHelper.constructPDFArray', 1)]

alloc = [('org.apache.fop.fo.properties.Property[]_[i]', 36), ('org/apache/fop/pdf/PDFNumber.doubleOut', 27), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.initWord', 24), ('org/apache/fop/image/loader/batik/PreloaderSVG.createImageInfo', 23), ('org.apache.fop.fo.FObj$FObjIterator_[i]', 22), ('org.apache.fop.traits.MinOptMax_[i]', 21), ('org.apache.fop.layoutmgr.BreakingAlgorithm$KnuthNode_[i]', 19), ('org/apache/fop/render/pdf/PDFImageHandlerSVG.handleImage', 18), ('org.apache.fop.fo.RecursiveCharIterator_[i]', 18), ('org/apache/fop/cli/InputHandler.transformTo', 14), ('org/apache/fop/fonts/FontTriplet.getKey', 14), ('org/apache/fop/pdf/PDFStream.setUp', 13), ('org.apache.fop.fo.FOText$TextCharIterator_[i]', 12), ('org/apache/fop/fo/properties/PropertyCache.fetch', 12), ('org/apache/fop/fonts/FontInfo.fontLookup', 12), ('org/apache/fop/layoutmgr/BreakingAlgorithm.createForcedNodes', 12), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.addElementsForASpace', 11), ('org.apache.fop.area.inline.WordArea_[i]', 11), ('org/apache/fop/image/loader/batik/PreloaderWMF.preloadImage', 10), ('org.apache.fop.fonts.GlyphMapping_[i]', 10), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.addWord', 10), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.getElementsForBreakingSpace', 9), ('org/apache/fop/fo/extensions/svg/SVGElementMapping.getAParserClassName', 9), ('org/apache/fop/pdf/PDFStream.streamHashCode', 8), ('org/apache/fop/image/loader/batik/PreloaderWMF.getImage', 8), ('org.apache.fop.layoutmgr.inline.KnuthInlineBox_[i]', 8), ('org.apache.fop.layoutmgr.KnuthGlue_[i]', 7), ('org.apache.fop.layoutmgr.KnuthPenalty_[i]', 7), ('org/apache/fop/svg/PDFBridgeContext.registerSVGBridges', 7), ('org/apache/fop/area/Area.addTrait', 7), ('org/apache/fop/complexscripts/bidi/DelimitedTextRange.<init>', 6), ('org/apache/fop/apps/FopFactoryBuilder.<init>', 6), ('org.apache.fop.util.CharUtilities$1_[i]', 6), ('org/apache/fop/fonts/FontInfo.getFontInstance', 6), ('org/apache/fop/pdf/PDFICCBasedColorSpace.setupsRGBColorProfile', 6), ('org/apache/fop/cli/InputHandler.getXMLReader', 6), ('org/apache/fop/fo/extensions/svg/BatikExtensionElementMapping.getAParserClassName', 6), ('org.apache.fop.fo.properties.CondLengthProperty_[i]', 6), ('org/apache/fop/pdf/PDFMetadata.outputRawStreamData', 6), ('org.apache.fop.traits.MinOptMax[]_[i]', 5), ('org/apache/fop/util/DelegatingContentHandler.startElement', 5), ('org.apache.fop.fonts.FontTriplet_[i]', 5), ('org/apache/fop/render/pdf/PDFGraphicsPainter.add', 5), ('org/apache/fop/events/EventFormatter.format', 5), ('org/apache/fop/cli/Main.startFOP', 5), ('org.apache.fop.fonts.Font[]_[i]', 5), ('org/apache/fop/render/intermediate/IFRenderer.createDefaultDocumentMetadata', 5), ('org/apache/fop/fo/FOElementMapping.initialize', 5), ('org/apache/fop/fonts/FontSelector.selectFontForCharactersInText', 5), ('org.apache.fop.fo.properties.CommonBorderPaddingBackground$BorderInfo_[i]', 4)]

wall = [('org/apache/fop/cli/InputHandler.transformTo', 3), ('org/apache/fop/util/text/AdvancedMessageFormat.parseInnerPattern', 2), ('org/apache/fop/image/loader/batik/PreloaderSVG.createImageInfo', 2), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.addAreas', 1), ('org/apache/fop/pdf/PDFDictionary.writeDictionary', 1), ('org/apache/fop/fo/properties/LineHeightPropertyMaker.convertProperty', 1), ('org/apache/fop/area/Area.getTrait', 1), ('org/apache/fop/layoutmgr/table/TableLayoutManager.registerColumnBackgroundArea', 1), ('org/apache/fop/fo/flow/table/TableCell.getNumberRowsSpanned', 1), ('org/apache/fop/pdf/PDFMetadata.updateInfoFromMetadata', 1), ('org/apache/fop/layoutmgr/KnuthPossPosIter.getLM', 1), ('org/apache/fop/layoutmgr/BalancingColumnBreakingAlgorithm.getElementIdBreaks', 1), ('org/apache/fop/render/intermediate/IFRenderer.restoreGraphicsState', 1), ('org/apache/fop/pdf/PDFColorHandler.<init>', 1), ('org/apache/fop/render/intermediate/IFRenderer.createDefaultDocumentMetadata', 1), ('org/apache/fop/fo/flow/Block.bind', 1), ('org/apache/fop/svg/PDFBridgeContext.registerSVGBridges', 1), ('org/apache/fop/image/loader/batik/BatikUtil.isBatikAvailable', 1), ('org/apache/fop/cli/CommandLineOptions.parse', 1), ('org/apache/fop/render/ps/PSImageHandlerSVG.shouldStrokeText', 1), ('org/apache/fop/layoutmgr/ListElement.<init>', 1), ('org/apache/fop/fo/XMLObj.addElement', 1), ('org/apache/fop/fo/FONode.setLocator', 1), ('org/apache/fop/fo/extensions/svg/SVGElementMapping.make', 1), ('org/apache/fop/layoutmgr/inline/PageNumberLayoutManager.getEffectiveArea', 1), ('org/apache/fop/layoutmgr/AbstractBreaker.doLayout', 1), ('org/apache/fop/cli/Main.startFOP', 1), ('org/apache/fop/layoutmgr/AbstractLayoutManager.getChildLMs', 1), ('org/apache/fop/fo/properties/PropertyCache.fetch', 1), ('org/apache/fop/fonts/FontTriplet.getKey', 1), ('org/apache/fop/fonts/Font.getWidth', 1), ('org/apache/fop/pdf/PDFMetadata.outputRawStreamData', 1), ('org/apache/fop/fo/FOElementMapping.initialize', 1), ('org/apache/fop/util/CompareUtil.equal', 1), ('org/apache/fop/svg/PDFGraphics2D.<init>', 1), ('org/apache/fop/fonts/FontTriplet.getStyle', 1), ('org/apache/fop/complexscripts/bidi/BidiResolver.resolveInlineDirectionality', 1), ('org/apache/fop/layoutmgr/Page.<init>', 1), ('org/apache/fop/events/DefaultEventBroadcaster.loadModel', 1), ('org/apache/fop/render/afp/extensions/AFPElementMapping.initialize', 1), ('org/apache/fop/pdf/PDFNumber.doubleOut', 1), ('org/apache/fop/fo/StaticPropertyList.get', 1), ('org/apache/fop/render/intermediate/AbstractIFPainter.drawImageUsingImageHandler', 1)]

itimer = [('org/apache/fop/render/pdf/PDFImageHandlerSVG.handleImage', 15), ('org/apache/fop/image/loader/batik/PreloaderSVG.createImageInfo', 6), ('org/apache/fop/apps/FopFactoryBuilder.<init>', 6), ('org/apache/fop/cli/InputHandler.transformTo', 6), ('org/apache/fop/fo/extensions/svg/SVGElementMapping.getAParserClassName', 4), ('org/apache/fop/fo/FOElementMapping.initialize', 4), ('org/apache/fop/render/intermediate/IFGraphicContext.<init>', 3), ('org/apache/fop/image/loader/batik/PreloaderWMF.preloadImage', 3), ('org/apache/fop/cli/CommandLineOptions.<init>', 3), ('org/apache/fop/render/intermediate/IFRenderer.createDefaultDocumentMetadata', 3), ('org/apache/fop/cli/Main.startFOP', 3), ('org/apache/fop/layoutmgr/inline/TextLayoutManager.getNextKnuthElements', 2), ('org/apache/fop/fonts/FontInfo.getInternalFontKey', 2), ('org/apache/fop/pdf/AbstractPDFStream.encodeAndWriteStream', 2), ('org/apache/fop/util/DelegatingContentHandler.startElement', 2), ('org/apache/fop/pdf/PDFNumber.doubleOut', 2), ('org/apache/fop/fonts/FontInfo.fontLookup', 2), ('org/apache/fop/fo/extensions/svg/SVGDOMContentHandlerFactory.startElement', 2), ('org/apache/fop/fo/XMLWhiteSpaceHandler.handleWhiteSpace', 2), ('org/apache/fop/pdf/InMemoryStreamCache.outputContents', 2), ('org/apache/fop/image/loader/batik/PreloaderWMF.getImage', 2), ('org/apache/fop/image/loader/batik/BatikUtil.isBatikAvailable', 2), ('org/apache/fop/render/PrintRendererConfigurator.<init>', 1), ('org/apache/fop/render/pdf/PDFPainter.fillRect', 1), ('org/apache/fop/fo/expr/PropertyParser.parsePrimaryExpr', 1), ('org/apache/fop/util/text/AdvancedMessageFormat.<init>', 1), ('org/apache/fop/fo/FOPropertyMapping.createShorthandProperties', 1), ('org/apache/fop/fo/flow/table/TableFObj.make', 1), ('org/apache/fop/layoutmgr/BlockLayoutManager.getParentArea', 1), ('org/apache/fop/fo/FOTreeBuilderContext.<init>', 1), ('org/apache/fop/pdf/PDFDocument.findPDFObject', 1), ('org/apache/fop/layoutmgr/BlockStackingLayoutManager.addLastVisibleMarks', 1), ('org/apache/fop/render/ps/PSImageHandlerSVG.<clinit>', 1), ('org/apache/fop/fo/flow/table/Table.<init>', 1), ('org/apache/fop/fo/PropertyList.get', 1), ('org/apache/fop/layoutmgr/inline/InlineLayoutManager.initialize', 1), ('org/apache/fop/util/XMLResourceBundle.handleGetXMLBundle', 1), ('org/apache/fop/layoutmgr/table/TableCellLayoutManager.getTableCell', 1), ('org/apache/fop/render/intermediate/AbstractIFPainter.drawImageUsingImageHandler', 1), ('org/apache/fop/layoutmgr/inline/LeafNodeLayoutManager.<clinit>', 1), ('org/apache/fop/fo/extensions/svg/SVGElement.getDimension', 1), ('org/apache/fop/layoutmgr/LayoutManagerMapping.makeFlowLayoutManager', 1), ('org/apache/fop/pdf/PDFDocument.encode', 1), ('org/apache/fop/fo/pagination/PageSequence.collectDelimitedTextRanges', 1), ('org/apache/fop/fonts/base14/HelveticaBold.<clinit>', 1), ('org/apache/fop/fo/FONode.getName', 1), ('org/apache/fop/fo/extensions/svg/SVGElementMapping.initialize', 1), ('org/apache/fop/image/loader/batik/BatikUtil.cloneSVGDocument', 1), ('org/apache/fop/layoutmgr/PageBreakingAlgorithm.computeDemerits', 1), ('org/apache/fop/render/AbstractRenderer.renderInlineViewport', 1)]

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
plt.title("Correlation Between Profiling Metrics - Fop")
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
plt.title("Jaccard Similarity Between Profiling Hotspots - Fop")
plt.show()
plt.savefig("Jaccard.png", bbox_inches="tight")
