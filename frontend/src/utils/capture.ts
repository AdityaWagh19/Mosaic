export async function captureSvgAsDataUrl(svgElement: SVGSVGElement | null): Promise<string | null> {
  if (!svgElement) return null;
  
  return new Promise((resolve) => {
    try {
      // Clone the SVG so we don't mutate the live DOM
      const clone = svgElement.cloneNode(true) as SVGSVGElement;
      
      // Ensure width/height are set explicitly for the canvas
      const width = svgElement.getBoundingClientRect().width || 800;
      const height = svgElement.getBoundingClientRect().height || 500;
      clone.setAttribute('width', String(width));
      clone.setAttribute('height', String(height));
      
      // Replace var(--color-*) with actual computed styles so the canvas can render them
      let xml = new XMLSerializer().serializeToString(clone);
      const computedStyles = getComputedStyle(document.documentElement);
      xml = xml.replace(/var\((--[^)]+)\)/g, (_, varName) => {
        return computedStyles.getPropertyValue(varName).trim() || '#000000';
      });

      const svg64 = btoa(unescape(encodeURIComponent(xml)));
      const b64Start = 'data:image/svg+xml;base64,';
      const image64 = b64Start + svg64;

      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, width, height);
          ctx.drawImage(img, 0, 0);
          resolve(canvas.toDataURL('image/png'));
        } else {
          resolve(null);
        }
      };
      img.onerror = () => resolve(null);
      img.src = image64;
    } catch (err) {
      console.error("Failed to capture SVG:", err);
      resolve(null);
    }
  });
}
