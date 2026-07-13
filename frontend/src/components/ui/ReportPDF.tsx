import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import type { RunResponse } from '../../types/models';

const styles = StyleSheet.create({
  page: { flexDirection: 'column', backgroundColor: '#ffffff', padding: 40, fontFamily: 'Helvetica' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 30, borderBottom: '2pt solid #000', paddingBottom: 15 },
  brand: { fontSize: 28, fontWeight: 'bold', color: '#000', letterSpacing: -1 },
  subtitle: { fontSize: 10, color: '#6b7280', textTransform: 'uppercase', letterSpacing: 1 },
  runInfo: { textAlign: 'right' },
  runId: { fontSize: 14, fontWeight: 'bold', color: '#111827' },
  date: { fontSize: 10, color: '#6b7280', marginTop: 4 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  card: { width: '48%', padding: 15, backgroundColor: '#f9fafb', borderRadius: 4, marginBottom: 15, border: '1pt solid #e5e7eb' },
  cardLabel: { fontSize: 10, color: '#6b7280', textTransform: 'uppercase', marginBottom: 4 },
  cardValue: { fontSize: 18, fontWeight: 'bold', color: '#111827' },
  section: { marginBottom: 25 },
  sectionTitle: { fontSize: 14, fontWeight: 'bold', color: '#111827', marginBottom: 10, borderBottom: '1pt solid #e5e7eb', paddingBottom: 5 },
  row: { flexDirection: 'row', paddingVertical: 6, borderBottom: '1pt solid #f3f4f6' },
  col1: { width: '40%', fontSize: 10, color: '#6b7280' },
  col2: { width: '60%', fontSize: 10, color: '#111827', fontWeight: 'bold' },
  conclusionBox: { backgroundColor: '#f0fdf4', border: '1pt solid #bbf7d0', padding: 15, borderRadius: 4, marginTop: 10 },
  conclusionTitle: { fontSize: 12, fontWeight: 'bold', color: '#166534', marginBottom: 8 },
  conclusionText: { fontSize: 11, color: '#15803d', lineHeight: 1.6 },
  footer: { position: 'absolute', bottom: 30, left: 40, right: 40, borderTop: '1pt solid #e5e7eb', paddingTop: 10, flexDirection: 'row', justifyContent: 'space-between' },
  footerText: { fontSize: 9, color: '#9ca3af' },
  definition: { marginBottom: 10 },
  defTerm: { fontSize: 10, fontWeight: 'bold', color: '#111827' },
  defDesc: { fontSize: 10, color: '#4b5563', lineHeight: 1.4 },
});

interface ReportPDFProps {
  result: RunResponse;
}

export function ReportPDF({ result }: ReportPDFProps) {
  const { config, metrics } = result;
  
  const conclusionText = metrics.converged 
    ? (metrics.termination_reason === 'stationarity' 
        ? `The population stabilized into a noisy equilibrium after ${metrics.convergence_time} steps. Final diversity was ${metrics.final_diversity.toFixed(3)}.` 
        : `All agent accents reached the model's consensus tolerance after ${metrics.convergence_time} steps. Final diversity was ${metrics.final_diversity.toFixed(3)}.`) 
    : `The population did not reach the model's convergence criteria within the ${result.config.T.toLocaleString()}-step limit. Final diversity was ${metrics.final_diversity.toFixed(3)}.`; 

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <View>
            <Text style={styles.brand}>Mosaic</Text>
            <Text style={styles.subtitle}>Simulation Report</Text>
          </View>
          <View style={styles.runInfo}>
            <Text style={styles.runId}>Run {result.run_id}</Text>
            <Text style={styles.date}>{new Date().toLocaleString()}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Results</Text>
          <View style={styles.grid}>
            <View style={styles.card}>
              <Text style={styles.cardLabel}>Run Status</Text>
              <Text style={styles.cardValue}>{metrics.converged ? 'Consensus Reached' : 'Max Steps Reached'}</Text>
            </View>
            <View style={styles.card}>
              <Text style={styles.cardLabel}>Convergence Time</Text>
              <Text style={styles.cardValue}>{metrics.converged ? `${metrics.convergence_time} steps` : 'N/A'}</Text>
            </View>
            <View style={styles.card}>
              <Text style={styles.cardLabel}>Final Diversity (H)</Text>
              <Text style={styles.cardValue}>{metrics.final_diversity.toFixed(3)}</Text>
            </View>
            <View style={styles.card}>
              <Text style={styles.cardLabel}>Pairwise Distance (D)</Text>
              <Text style={styles.cardValue}>{metrics.final_pairwise_distance.toFixed(3)}</Text>
            </View>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Model Configuration</Text>
          <View style={styles.row}><Text style={styles.col1}>Topology</Text><Text style={styles.col2}>{config.topology}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>N (Population)</Text><Text style={styles.col2}>{config.N}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>T (Interaction Limit)</Text><Text style={styles.col2}>{config.T}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>Gamma (Prestige Weight)</Text><Text style={styles.col2}>{config.gamma}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>Theta (Confidence Bound)</Text><Text style={styles.col2}>{config.theta}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>Sigma (Drift Noise)</Text><Text style={styles.col2}>{config.sigma}</Text></View>
          <View style={styles.row}><Text style={styles.col1}>Random Seed</Text><Text style={styles.col2}>{config.seed}</Text></View>
        </View>
        
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Conclusion & Interpretation</Text>
          <View style={styles.conclusionBox}>
            <Text style={styles.conclusionTitle}>Run Summary</Text>
            <Text style={styles.conclusionText}>{conclusionText}</Text>
          </View>
        </View>

        <View style={styles.footer} fixed>
          <Text style={styles.footerText}>Mosaic Simulation Platform</Text>
          <Text style={styles.footerText} render={({ pageNumber, totalPages }) => `Page ${pageNumber} of ${totalPages}`} />
        </View>
      </Page>
    </Document>
  );
}
