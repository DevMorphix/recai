import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import type { PdfTemplate } from './pdfTemplates';

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function markdownToStyledHtml(text: string, textColor: string): string {
  return escapeHtml(text)
    .replace(/^### (.*$)/gim, `<h3 style="font-size:16px;font-weight:600;margin:16px 0 8px;color:${textColor}">$1</h3>`)
    .replace(/^## (.*$)/gim, `<h2 style="font-size:18px;font-weight:600;margin:20px 0 10px;color:${textColor}">$1</h2>`)
    .replace(/^# (.*$)/gim, `<h1 style="font-size:22px;font-weight:700;margin:24px 0 12px;color:${textColor}">$1</h1>`)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gim, `<div style="display:flex;margin-bottom:6px;color:${textColor}"><span style="margin-right:8px">&#8226;</span><span>$1</span></div>`)
    .replace(/^\* (.*$)/gim, `<div style="display:flex;margin-bottom:6px;color:${textColor}"><span style="margin-right:8px">&#8226;</span><span>$1</span></div>`)
    .replace(/^(\d+)\. (.*$)/gim, `<div style="display:flex;margin-bottom:6px;color:${textColor}"><span style="min-width:24px">$1.</span><span>$2</span></div>`)
    .replace(/^---$/gim, '<hr style="margin:20px 0;border:none;border-top:1px solid #e5e7eb">')
    .replace(/\n/g, '<br>');
}

function buildHeaderStyles(template: PdfTemplate) {
  const base = template.headerStyle === 'centered' ? 'text-align:center;' : '';
  const border = template.headerStyle === 'underlined'
    ? `border-bottom:3px solid ${template.accentColor};`
    : '';
  const bg = template.headerStyle === 'boxed'
    ? `background:${template.accentColor}15;border-radius:8px;padding:20px;margin:-20px -20px 24px -20px;`
    : '';
  return { base, border, bg };
}

async function renderPdfBlob(
  title: string,
  date: string,
  markdownContent: string,
  template: PdfTemplate,
  logoBase64: string | null,
  footerText: string
): Promise<Blob> {
  const renderWidth = 800;
  const formattedContent = markdownToStyledHtml(markdownContent, template.textColor);
  const { base: headerAlign, border: headerBorder, bg: headerBg } = buildHeaderStyles(template);

  const logoHtml = logoBase64
    ? `<img src="${logoBase64}" style="max-height:60px;max-width:200px;margin-bottom:16px;display:block;" />`
    : '';

  const tempContainer = document.createElement('div');
  tempContainer.style.cssText = `position:absolute;left:-9999px;top:0;width:${renderWidth}px;padding:20px;background:#ffffff;font-family:system-ui,-apple-system,sans-serif;box-sizing:border-box;`;

  tempContainer.innerHTML = `
    ${logoHtml}
    <div style="${headerBg}${headerBorder}padding-bottom:20px;margin-bottom:28px;${headerAlign}">
      <h1 style="font-size:26px;font-weight:700;margin:0 0 10px;color:${template.textColor}">${escapeHtml(title)}</h1>
      <p style="font-size:14px;color:#6b7280;margin:0">${escapeHtml(date)}</p>
    </div>
    <div style="color:${template.textColor};line-height:1.8;font-size:14px">
      ${formattedContent}
    </div>
    <div style="margin-top:48px;padding-top:20px;border-top:1px solid #e5e7eb;font-size:12px;color:#9ca3af;${headerAlign}">
      ${escapeHtml(footerText)} &bull; ${new Date().toLocaleDateString()}
    </div>
  `;

  document.body.appendChild(tempContainer);

  try {
    const canvas = await html2canvas(tempContainer, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    });

    const marginMm = 5;
    const pageWidthMm = 210;
    const pageHeightMm = 297;
    const contentWidthMm = pageWidthMm - marginMm * 2;
    const contentHeightMm = pageHeightMm - marginMm * 2;

    const imgWidthMm = contentWidthMm;
    const imgHeightMm = (canvas.height * contentWidthMm) / canvas.width;

    const pdf = new jsPDF('p', 'mm', 'a4');

    if (imgHeightMm <= contentHeightMm) {
      pdf.addImage(canvas.toDataURL('image/jpeg', 0.95), 'JPEG', marginMm, marginMm, imgWidthMm, imgHeightMm);
    } else {
      const pxPerMm = canvas.width / contentWidthMm;
      const pageHeightPx = contentHeightMm * pxPerMm;
      const totalPages = Math.ceil(canvas.height / pageHeightPx);

      for (let i = 0; i < totalPages; i++) {
        if (i > 0) pdf.addPage();

        const srcY = i * pageHeightPx;
        const srcH = Math.min(pageHeightPx, canvas.height - srcY);

        const pageCanvas = document.createElement('canvas');
        pageCanvas.width = canvas.width;
        pageCanvas.height = srcH;

        const ctx = pageCanvas.getContext('2d')!;
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, pageCanvas.width, pageCanvas.height);
        ctx.drawImage(canvas, 0, srcY, canvas.width, srcH, 0, 0, canvas.width, srcH);

        const sliceHeightMm = srcH / pxPerMm;
        pdf.addImage(pageCanvas.toDataURL('image/jpeg', 0.95), 'JPEG', marginMm, marginMm, imgWidthMm, sliceHeightMm);
      }
    }

    return pdf.output('blob');
  } finally {
    document.body.removeChild(tempContainer);
  }
}

export async function generateMinutesPdf(
  title: string,
  date: string,
  markdownContent: string,
  template: PdfTemplate,
  logoBase64?: string | null
): Promise<Blob> {
  return renderPdfBlob(title, date, markdownContent, template, logoBase64 || null, 'Generated by Rec AI');
}

export async function generateSummaryPdf(
  title: string,
  date: string,
  markdownContent: string
): Promise<Blob> {
  const fixedTemplate: PdfTemplate = {
    name: 'Summary',
    accentColor: '#16a34a',
    textColor: '#111827',
    headerStyle: 'underlined',
    isDefault: true
  };
  return renderPdfBlob(title, date, markdownContent, fixedTemplate, null, 'Built with Rec AI');
}
