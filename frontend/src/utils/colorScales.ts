// To adhere strictly to the monochrome design system, we want to map clusters
// to varying shades of Ink, Stone, Paper Warm, or similar low-chroma colors.
// Since D3 categorical colors are usually high-chroma, we will define our own 
// low-chroma array based on design.md tokens.

const MONOCHROME_PALETTE = [
  '#272421', // Ink
  '#7d7c7a', // Stone
  '#a3a2a0', // Lighter Stone
  '#504e4c', // Darker Stone
  '#333333'  // Charcoal
];

export const getClusterColor = (clusterId: number) => {
  // Use modulo to safely wrap around if there are more than 5 clusters
  return MONOCHROME_PALETTE[clusterId % MONOCHROME_PALETTE.length];
};
