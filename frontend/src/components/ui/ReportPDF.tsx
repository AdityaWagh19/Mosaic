import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import type { RunResponse } from '../../types/models';

const styles = StyleSheet.create({
  page: {
    flexDirection: 'column',
    backgroundColor: '#ffffff',
    padding: 40,
    fontFamily: 'Helvetica',
  },
  header: {
    marginBottom: 30,
    borderBottom: '1pt solid #e5e7eb',
    paddingBottom: 15,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 12,
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#374151',
    marginBottom: 10,
    borderBottom: '1pt solid #f3f4f6',
    paddingBottom: 5,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  label: {
    fontSize: 11,
    color: '#6b7280',
  },
  value: {
    fontSize: 11,
    color: '#111827',
    fontWeight: 'bold',
  },
  text: {
    fontSize: 11,
    color: '#4b5563',
    lineHeight: 1.5,
  }
});

export function ReportPDF({ result }: { result: RunResponse }) {
  const { config, metrics } = result;

  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <View style={styles.header}>
          <Text style={styles.subtitle}>Mosaic Simulation Report</Text>
          <Text style={styles.title}>Run {result.run_id}</Text>
          <Text style={styles.label}>Generated on {new Date().toLocaleDateString()}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Configuration Parameters</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Topology</Text>
            <Text style={styles.value}>{config.topology}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>N (Speakers)</Text>
            <Text style={styles.value}>{config.N}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>T (Max Steps)</Text>
            <Text style={styles.value}>{config.T}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Gamma (Prestige)</Text>
            <Text style={styles.value}>{config.gamma}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Theta (Confidence)</Text>
            <Text style={styles.value}>{config.theta}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Sigma (Drift)</Text>
            <Text style={styles.value}>{config.sigma}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Seed</Text>
            <Text style={styles.value}>{config.seed}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Final Metrics</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Status</Text>
            <Text style={styles.value}>{metrics.converged ? 'Converged' : 'Max steps reached'}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Convergence Time</Text>
            <Text style={styles.value}>{metrics.converged ? `${metrics.convergence_time} steps` : 'N/A'}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Final Diversity (H)</Text>
            <Text style={styles.value}>{metrics.final_diversity.toFixed(3)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Final Pairwise Distance</Text>
            <Text style={styles.value}>{metrics.final_pairwise_distance.toFixed(3)}</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Interpretation</Text>
          <Text style={styles.text}>
            {metrics.converged 
              ? `The population reached a stable state after ${metrics.convergence_time} steps. Final diversity was ${metrics.final_diversity.toFixed(3)}, indicating how evenly accent clusters remained represented.`
              : `The population was still changing when the ${config.T}-step limit was reached. Final diversity was ${metrics.final_diversity.toFixed(3)}; inspect the trajectory to see whether groups were still separating or moving together.`}
          </Text>
        </View>
      </Page>
    </Document>
  );
}
