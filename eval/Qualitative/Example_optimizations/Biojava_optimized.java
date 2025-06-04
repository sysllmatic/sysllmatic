
package org.biojava.nbio.aaproperties;

import org.biojava.nbio.aaproperties.xml.AminoAcidCompositionTable;
import org.biojava.nbio.aaproperties.xml.CaseFreeAminoAcidCompoundSet;
import org.biojava.nbio.core.exceptions.CompoundNotFoundException;
import org.biojava.nbio.core.sequence.ProteinSequence;
import org.biojava.nbio.core.sequence.compound.AminoAcidCompound;
import org.biojava.nbio.core.sequence.compound.AminoAcidCompoundSet;
import org.biojava.nbio.core.sequence.io.*;
import org.biojava.nbio.core.sequence.template.CompoundSet;

import java.io.*;
import java.util.*;
import java.util.Map.Entry;
import java.util.concurrent.*;

public class CommandPrompt {

    public static void main(String[] args) throws Exception{
        run(args);
    }

    private static AminoAcidCompositionTable checkForValidityAndObtainAATable(String inputLocation, int propertyListSize, String aminoAcidCompositionLocation,
            String elementMassLocation) throws Exception{
        if(inputLocation == null) {
            showHelp();
            throw new Error("Please do provide location of input file.");
        }
        if(propertyListSize == 0){
            showHelp();
            throw new Error("Please at least specify a property to compute.");
        }
        AminoAcidCompositionTable aaTable = null;
        if(aminoAcidCompositionLocation != null && elementMassLocation == null){
            aaTable = PeptideProperties.obtainAminoAcidCompositionTable(new File(aminoAcidCompositionLocation));
        }else if(aminoAcidCompositionLocation != null && elementMassLocation != null){
            aaTable = PeptideProperties.obtainAminoAcidCompositionTable(new File(aminoAcidCompositionLocation, elementMassLocation));
        }else if(aminoAcidCompositionLocation == null && elementMassLocation != null){
            throw new Error("You have define the location of Element Mass XML file. Please also define the location of Amino Acid Composition XML file");
        }
        return aaTable;
    }

    private static void readInputAndGenerateOutput(String outputLocation, List<Character> propertyList, List<Character> specificList,
            String delimiter, String inputLocation, AminoAcidCompositionTable aaTable, int decimalPlace) throws Exception{
        final int THREADS = Runtime.getRuntime().availableProcessors();
        BufferedWriter output;
        boolean closeOutput = false;
        if(outputLocation != null) {
            output = new BufferedWriter(new FileWriter(outputLocation));
            closeOutput = true;
        } else {
            output = new BufferedWriter(new OutputStreamWriter(System.out));
        }
        printHeader(output, propertyList, specificList, delimiter);

        CompoundSet<AminoAcidCompound> set = (aaTable == null)
            ? CaseFreeAminoAcidCompoundSet.getAminoAcidCompoundSet()
            : aaTable.getAminoAcidCompoundSet();

        
        boolean isGenbank = inputLocation.toLowerCase().contains(".gb");
        InputStream inStream = new FileInputStream(inputLocation);
        Iterator<Entry<String, ProteinSequence>> iterator;
        if (isGenbank) {
            GenbankReader<ProteinSequence, AminoAcidCompound> genbankReader = new GenbankReader<>(
                    inStream, new GenericGenbankHeaderParser<>(), new ProteinSequenceCreator(set));
            iterator = genbankReader.process().entrySet().iterator();
        } else {
            FastaReader<ProteinSequence, AminoAcidCompound> fastaReader = new FastaReader<>(
                    inStream, new GenericFastaHeaderParser<>(), new ProteinSequenceCreator(set));
            iterator = fastaReader.process().entrySet().iterator();
        }

        List<Entry<String, ProteinSequence>> entries = new ArrayList<>();
        while (iterator.hasNext()) {
            entries.add(iterator.next());
        }
        int totalSequences = entries.size();
        int fivePercent = (totalSequences == 0) ? 1 : Math.max(1, totalSequences / 20);

        
        ExecutorService pool = Executors.newFixedThreadPool(THREADS);
        List<Future<String>> results = new ArrayList<>(totalSequences);
        IPeptideProperties pp = new PeptidePropertiesImpl();
        for (int i = 0; i < entries.size(); i++) {
            final Entry<String, ProteinSequence> entry = entries.get(i);
            final int seqIndex = i;
            results.add(pool.submit(() -> {
                StringBuilder rowBuilder = new StringBuilder(1024);
                double[] dList = new double[64];
                int dCount = computeRow(rowBuilder, dList, entry.getValue().getOriginalHeader(), entry.getValue().getSequenceAsString().trim(), delimiter, aaTable, propertyList, specificList, decimalPlace, pp);
                return rowBuilder.toString();
            }));
        }

        pool.shutdown();

        
        int count = 0;
        for (Future<String> f : results) {
            output.write(f.get());
            count++;
            if (fivePercent == 0)
                System.out.print("Processing sequences: "+count+"\r");
            else if (count % fivePercent == 0) {
                int percentage = 5 * (count / fivePercent);
                System.out.print("Processing sequences: "+percentage+"%\r");
            }
        }
        System.out.println();
        if (closeOutput) {
            output.close();
        } else {
            output.flush();
        }
    }

    public static void run(String[] args) throws Exception{
        List<Character> propertyList = new ArrayList<Character>();
        List<Character> specificList = new ArrayList<Character>();
        String inputLocation = null;
        String outputLocation = null;
        String aminoAcidCompositionLocation = null;
        String elementMassLocation = null;
        String delimiter = ",";
        int decimalPlace = 4;

        for(int i = 0; i < args.length; i++){
            if(args[i].charAt(0) != '-' || args[i].length() != 2){
                showHelp();
                throw new Error("Unknown option: " + args[i]);
            }else{
                switch(args[i].charAt(1)){
                case 'i': inputLocation = args[++i]; break;
                case 'o': outputLocation = args[++i]; break;
                case 'f':
                    i++;
                    if("csv".equalsIgnoreCase(args[i])) delimiter = ",";
                    else if("tsv".equalsIgnoreCase(args[i])) delimiter = "\t";
                    else throw new Error("Invalid value for -f: " + args[i] + ". Please choose either csv or tsv only.");
                    break;
                case 'x': aminoAcidCompositionLocation = args[++i]; break;
                case 'y': elementMassLocation = args[++i]; break;
                case 'd': decimalPlace = Integer.parseInt(args[++i]); break;
                case 'a':
                    propertyList.add('1');propertyList.add('2');propertyList.add('3');propertyList.add('4');propertyList.add('5');propertyList.add('6');propertyList.add('7');propertyList.add('8');propertyList.add('9');
                    break;
                case '1': propertyList.add('1'); break;
                case '2': propertyList.add('2'); break;
                case '3': propertyList.add('3'); break;
                case '4': propertyList.add('4'); break;
                case '5': propertyList.add('5'); break;
                case '6': propertyList.add('6'); break;
                case '7': propertyList.add('7'); break;
                case '8': propertyList.add('8'); break;
                case '9': propertyList.add('9'); break;
                case '0':
                    propertyList.add('0');
                    i++;
                    if(args[i].length() != 1) throw new Error("Invalid value: " + args[i] + ". Amino Acid Symbol should be of single character");
                    specificList.add(args[i].toUpperCase().charAt(0));
                    break;
                default:
                    showHelp();
                    throw new Error("Unknown option: " + args[i]);
                }
            }
        }
        AminoAcidCompositionTable aaTable = checkForValidityAndObtainAATable(inputLocation, propertyList.size(), aminoAcidCompositionLocation,
                elementMassLocation);
        readInputAndGenerateOutput(outputLocation, propertyList, specificList, delimiter, inputLocation, aaTable, decimalPlace);
    }

    
    private static void printHeader(BufferedWriter output, List<Character> propertyList, List<Character> specificList, String delimiter) throws IOException{
        int specificCount = 0;
        List<String> sList = new ArrayList<String>();
        sList.add("SequenceName");
        for(Character c:propertyList){
            switch(c){
            case '1': sList.add(PropertyName.MolecularWeight.toString()); break;
            case '2': sList.add(PropertyName.Absorbance_True.toString()); sList.add(PropertyName.Absorbance_False.toString()); break;
            case '3': sList.add(PropertyName.ExtinctionCoefficient_True.toString()); sList.add(PropertyName.ExtinctionCoefficient_False.toString()); break;
            case '4': sList.add(PropertyName.InstabilityIndex.toString()); break;
            case '5': sList.add(PropertyName.ApliphaticIndex.toString()); break;
            case '6': sList.add(PropertyName.AverageHydropathyValue.toString()); break;
            case '7': sList.add(PropertyName.IsoelectricPoint.toString()); break;
            case '8': sList.add(PropertyName.NetCharge_pH_7.toString()); break;
            case '9':
                sList.add(PropertyName.A.toString()); sList.add(PropertyName.R.toString());
                sList.add(PropertyName.N.toString()); sList.add(PropertyName.D.toString());
                sList.add(PropertyName.C.toString()); sList.add(PropertyName.E.toString());
                sList.add(PropertyName.Q.toString()); sList.add(PropertyName.G.toString());
                sList.add(PropertyName.H.toString()); sList.add(PropertyName.I.toString());
                sList.add(PropertyName.L.toString()); sList.add(PropertyName.K.toString());
                sList.add(PropertyName.M.toString()); sList.add(PropertyName.F.toString());
                sList.add(PropertyName.P.toString()); sList.add(PropertyName.S.toString());
                sList.add(PropertyName.T.toString()); sList.add(PropertyName.W.toString());
                sList.add(PropertyName.Y.toString()); sList.add(PropertyName.V.toString());
                break;
            case '0': sList.add("" + specificList.get(specificCount++)); break;
            }
        }
        for(int i = 0; i < sList.size(); i++){
            if(i != 0) output.write(delimiter);
            output.write(sList.get(i));
        }
        output.newLine();
        output.flush();
    }

    public enum PropertyName{MolecularWeight, Absorbance_True, Absorbance_False, ExtinctionCoefficient_True, ExtinctionCoefficient_False,
        InstabilityIndex, ApliphaticIndex, AverageHydropathyValue, IsoelectricPoint, NetCharge_pH_7, A, R,
        N, D, C, E, Q, G, H, I, L,
        K, M, F, P, S, T, W, Y, V};

    
    private static int computeRow(StringBuilder rowBuilder, double[] dList, String header, String sequence, String delimiter,
            AminoAcidCompositionTable aaTable, List<Character> propertyList, List<Character> specificList, int decimalPlace, IPeptideProperties pp) throws CompoundNotFoundException {
        ProteinSequence pSequence;
        CompoundSet<AminoAcidCompound> aaSet;
        if(aaTable != null){
            sequence = Utils.checkSequence(sequence, aaTable.getSymbolSet());
            pSequence = new ProteinSequence(sequence, aaTable.getAminoAcidCompoundSet());
            aaSet = aaTable.getAminoAcidCompoundSet();
        }else{
            sequence = Utils.checkSequence(sequence);
            pSequence = new ProteinSequence(sequence);
            aaSet = AminoAcidCompoundSet.getAminoAcidCompoundSet();
        }
        int dCount = 0;
        int specificCount = 0;
        for(Character c:propertyList){
            switch(c){
            case '1':
                dList[dCount++] = pp.getMolecularWeight(pSequence);
                break;
            case '2':
                dList[dCount++] = pp.getAbsorbance(pSequence, true);
                dList[dCount++] = pp.getAbsorbance(pSequence, false);
                break;
            case '3':
                dList[dCount++] = pp.getExtinctionCoefficient(pSequence, true);
                dList[dCount++] = pp.getExtinctionCoefficient(pSequence, false);
                break;
            case '4': dList[dCount++] = pp.getInstabilityIndex(pSequence); break;
            case '5': dList[dCount++] = pp.getApliphaticIndex(pSequence); break;
            case '6': dList[dCount++] = pp.getAvgHydropathy(pSequence); break;
            case '7': dList[dCount++] = pp.getIsoelectricPoint(pSequence); break;
            case '8': dList[dCount++] = pp.getNetCharge(pSequence); break;
            case '9':
                Map<AminoAcidCompound, Double> aaCompound2Double = pp.getAAComposition(pSequence);
                dList[dCount++] = aaCompound2Double.get(Constraints.A); dList[dCount++] = aaCompound2Double.get(Constraints.R);
                dList[dCount++] = aaCompound2Double.get(Constraints.N); dList[dCount++] = aaCompound2Double.get(Constraints.D);
                dList[dCount++] = aaCompound2Double.get(Constraints.C); dList[dCount++] = aaCompound2Double.get(Constraints.E);
                dList[dCount++] = aaCompound2Double.get(Constraints.Q); dList[dCount++] = aaCompound2Double.get(Constraints.G);
                dList[dCount++] = aaCompound2Double.get(Constraints.H); dList[dCount++] = aaCompound2Double.get(Constraints.I);
                dList[dCount++] = aaCompound2Double.get(Constraints.L); dList[dCount++] = aaCompound2Double.get(Constraints.K);
                dList[dCount++] = aaCompound2Double.get(Constraints.M); dList[dCount++] = aaCompound2Double.get(Constraints.F);
                dList[dCount++] = aaCompound2Double.get(Constraints.P); dList[dCount++] = aaCompound2Double.get(Constraints.S);
                dList[dCount++] = aaCompound2Double.get(Constraints.T); dList[dCount++] = aaCompound2Double.get(Constraints.W);
                dList[dCount++] = aaCompound2Double.get(Constraints.Y); dList[dCount++] = aaCompound2Double.get(Constraints.V);
                break;
            case '0':
                dList[dCount++] = pp.getEnrichment(pSequence, aaSet.getCompoundForString("" + specificList.get(specificCount++)));
                break;
            }
        }
        rowBuilder.append(header.replace(delimiter, "_"));
        for(int i=0; i<dCount; i++) {
            rowBuilder.append(delimiter);
            rowBuilder.append(Utils.roundToDecimals(dList[i], decimalPlace));
        }
        rowBuilder.append('\n');
        return dCount;
    }

    private static void showHelp(){
        System.err.println("NAME");
        System.err.println("\tAn executable to generate physico-chemical properties of protein sequences.");
        System.err.println();
        System.err.println("EXAMPLES");
        System.err.println("\tjava -jar AAProperties.jar -i test.fasta -a");
        System.err.println("\t\tGenerates all possible properties.");
        System.err.println();
        System.err.println("\tjava -jar AAProperties.jar -i test.fasta -1 -3 -7");
        System.err.println("\t\tGenerates only molecular weight, extinction coefficient and isoelectric point.");
        System.err.println();
        System.err.println("\tjava -jar AAProperties.jar -i test.fasta -0 A -0 N -1");
        System.err.println("\t\tGenerates composition of two specific amino acid symbol and molecular weight.");
        System.err.println();
        System.err.println("OPTIONS");
        System.err.println("\tRequired");
        System.err.println("\t\t-i location of input FASTA file");
        System.err.println();
        System.err.println("\tOptional");
        System.err.println("\t\t-o location of output file [standard output (default)]");
        System.err.println("\t\t-f output format [csv (default) or tsv]");
        System.err.println("\t\t-x location of Amino Acid Composition XML file for defining amino acid composition");
        System.err.println("\t\t-y location of Element Mass XML file for defining mass of elements");
        System.err.println("\t\t-d number of decimals (int) [4 (default)]");
        System.err.println();
        System.err.println("\tProvide at least one of them");
        System.err.println("\t\t-a compute properties of option 1-9");
        System.err.println("\t\t-1 compute molecular weight");
        System.err.println("\t\t-2 compute absorbance");
        System.err.println("\t\t-3 compute extinction coefficient");
        System.err.println("\t\t-4 compute instability index");
        System.err.println("\t\t-5 compute apliphatic index");
        System.err.println("\t\t-6 compute average hydropathy value");
        System.err.println("\t\t-7 compute isoelectric point");
        System.err.println("\t\t-8 compute net charge at pH 7");
        System.err.println("\t\t-9 compute composition of 20 standard amino acid (A, R, N, D, C, E, Q, G, H, I, L, K, M, F, P, S, T, W, Y, V)");
        System.err.println("\t\t-0 compute composition of specific amino acid symbol");
        System.err.println();
    }
}
