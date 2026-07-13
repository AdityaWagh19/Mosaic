import { Document, Page, Text, View, StyleSheet, Image } from '@react-pdf/renderer';
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
  text: { fontSize: 11, color: '#4b5563', lineHeight: 1.6 },
  imageContainer: { width: '100%', height: 300, backgroundColor: '#f9fafb', border: '1pt solid #e5e7eb', borderRadius: 4, marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  image: { objectFit: 'contain', width: '100%', height: '100%' },
  footer: { position: 'absolute', bottom: 30, left: 40, right: 40, borderTop: '1pt solid #e5e7eb', paddingTop: 10, flexDirection: 'row', justifyContent: 'space-between' },
  footerText: { fontSize: 9, color: '#9ca3af' },
  definition: { marginBottom: 10 },
  defTerm: { fontSize: 10, fontWeight: 'bold', color: '#111827' },
  defDesc: { fontSize: 10, color: '#4b5563', lineHeight: 1.4 },
});

interface ReportPDFProps {
  result: RunResponse;
  networkImage?: string;
  umapImage?: string;
  timelineImage?: string;
}

export function ReportPDF({ result, networkImage, umapImage, timelineImage }: ReportPDFProps) {
  const { config, metrics } = result;

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

        {timelineImage && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Evidence over time</Text>
            <View style={{ ...styles.imageContainer, height: 180 }}>
              <Image src={timelineImage} style={styles.image} />
            </View>
          </View>
        )}

        <View style={styles.footer}>
          <Text style={styles.footerText}>Mosaic Simulation Platform</Text>
          <Text style={styles.footerText}>Page 1 of 2</Text>
        </View>
      </Page>

      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <View>
            <Text style={styles.brand}>Mosaic</Text>
            <Text style={styles.subtitle}>Artifact Evidence</Text>
          </View>
        </View>

        {networkImage && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Social Network Structure</Text>
            <View style={styles.imageContainer}>
              <Image src={networkImage} style={styles.image} />
            </View>
          </View>
        )}

        {umapImage && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Final Accent Space (UMAP)</Text>
            <View style={styles.imageContainer}>
              <Image src={umapImage} style={styles.image} />
            </View>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Metric Definitions</Text>
          <View style={styles.definition}>
            <Text style={styles.defTerm}>Consensus Tolerance</Text>
            <Text style={styles.defDesc}>The simulation halts when all agents are within a fixed maximum pairwise distance threshold, avoiding false diversity driven by floating-point KMeans noise.</Text>
          </View>
          <View style={styles.definition}>
            <Text style={styles.defTerm}>Diversity (H)</Text>
            <Text style={styles.defDesc}>Shannon entropy calculated across accent clusters. At consensus, H is exactly 0.0.</Text>
          </View>
          <View style={styles.definition}>
            <Text style={styles.defTerm}>Pairwise Distance (D)</Text>
            <Text style={styles.defDesc}>The average L2 separation between all pairs of agent accent vectors.</Text>
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Run ID: {result.run_id}</Text>
          <Text style={styles.footerText}>Page 2 of 2</Text>
        </View>
      </Page>
    </Document>
  );
}
