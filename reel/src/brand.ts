import {staticFile} from 'remotion';
import '@fontsource/inter/800.css';
import '@fontsource/inter/900.css';
import '@fontsource/cairo/700.css';
import '@fontsource/cairo/800.css';

export const BRAND = {
	orange: '#F25A24',
	orangeLight: '#FF8A4C',
	orangeDark: '#A93309',
	white: '#FFFFFF',
	dark: '#0E0D0C',
	glassDark: 'rgba(12,12,12,0.42)',
	bevel: '#C9D6E8',
	cream: '#F4EFE6',
	gold: '#FFD447',
	goldDeep: '#E0A106',
	yellow: '#FFC629',
	green: '#2BD576',
};

/**
 * Arabic: Thmanyah Sans Bold from public/fonts/ThmanyahSans-Bold.ttf when present;
 * the browser falls back to Cairo (bundled) if that file is missing.
 */
export const AR_FONT = "'Thmanyah Sans', 'Cairo', sans-serif";
export const EN_FONT = "'Inter', sans-serif";

export const fontFaceCss = `
@font-face {
  font-family: 'Thmanyah Sans';
  src: url('${staticFile('fonts/ThmanyahSans-Bold.woff2')}') format('woff2'),
       url('${staticFile('fonts/ThmanyahSans-Bold.ttf')}') format('truetype'),
       url('${staticFile('fonts/ThmanyahSans-Bold.otf')}') format('opentype');
  font-weight: 700 900;
}`;

export const SAFE = {
	platformUi: [0, 200],
	annotations: [200, 420],
	face: [420, 1500],
	captions: [1560, 1800],
};
