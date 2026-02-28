import { Preferences } from '@capacitor/preferences';

export interface PdfTemplate {
  name: string;
  accentColor: string;
  textColor: string;
  headerStyle: 'simple' | 'underlined' | 'boxed' | 'centered';
  isDefault: boolean;
}

export const defaultTemplates: Record<string, PdfTemplate> = {
  professional: {
    name: 'Professional',
    accentColor: '#16a34a',
    textColor: '#111827',
    headerStyle: 'underlined',
    isDefault: true
  },
  minimal: {
    name: 'Minimal',
    accentColor: '#6b7280',
    textColor: '#374151',
    headerStyle: 'simple',
    isDefault: true
  },
  corporate: {
    name: 'Corporate',
    accentColor: '#2563eb',
    textColor: '#1e293b',
    headerStyle: 'boxed',
    isDefault: true
  },
  creative: {
    name: 'Creative',
    accentColor: '#9333ea',
    textColor: '#111827',
    headerStyle: 'centered',
    isDefault: true
  }
};

const TEMPLATES_KEY = 'pdfTemplates';
const LOGO_KEY = 'pdfLogo';

export async function loadTemplates(): Promise<Record<string, PdfTemplate>> {
  const { value } = await Preferences.get({ key: TEMPLATES_KEY });
  if (value) {
    return { ...defaultTemplates, ...JSON.parse(value) };
  }
  return { ...defaultTemplates };
}

export async function saveCustomTemplates(
  allTemplates: Record<string, PdfTemplate>
): Promise<void> {
  const custom: Record<string, PdfTemplate> = {};
  Object.entries(allTemplates).forEach(([key, val]) => {
    if (!val.isDefault) custom[key] = val;
  });
  await Preferences.set({ key: TEMPLATES_KEY, value: JSON.stringify(custom) });
}

export async function loadLogo(): Promise<string | null> {
  const { value } = await Preferences.get({ key: LOGO_KEY });
  return value;
}

export async function saveLogo(base64: string): Promise<void> {
  await Preferences.set({ key: LOGO_KEY, value: base64 });
}

export async function removeLogo(): Promise<void> {
  await Preferences.remove({ key: LOGO_KEY });
}
