import React, {useEffect, useLayoutEffect, useRef, useState} from 'react';
import {continueRender, delayRender, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {AR_FONT, BRAND, EN_FONT} from './brand';
import {Glass} from './Glass';
import type {CaptionGroup, Word} from './types';

/** Instagram-safe: below the mouth (<= ~1200) and above the username/caption UI (>= ~1500). */
const TOP = 1250;
const MAX_W = 800;

const whiteCrystal = [
	`0 2px 0 ${BRAND.bevel}`,
	'0 4px 0 rgba(110,130,160,0.55)',
	'0 0 2px rgba(255,255,255,0.9)',
	'0 12px 24px rgba(0,0,0,0.65)',
].join(', ');

const goldCrystal = [
	`0 2px 0 ${BRAND.goldDeep}`,
	'0 4px 0 rgba(150,100,0,0.7)',
	'0 0 28px rgba(255,212,71,0.7)',
	'0 12px 24px rgba(0,0,0,0.6)',
].join(', ');

/** English line: «keyword» in yellow. */
const EnLine: React.FC<{text: string}> = ({text}) => {
	const parts = text.toUpperCase().split(/(«[^»]+»)/g);
	return (
		<>
			{parts.map((p, i) =>
				p.startsWith('«') ? (
					<span key={i} style={{color: BRAND.yellow}}>
						{p.slice(1, -1)}
					</span>
				) : (
					<span key={i}>{p}</span>
				),
			)}
		</>
	);
};

export const Captions: React.FC<{groups: CaptionGroup[]; words: Word[]}> = ({groups, words}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	const g = groups.find((c) => t >= c.start && t < c.end);
	// the size estimate below runs short for wide Arabic letters (ف ك ش): measure the words and shrink to MAX_W if needed
	const rowRef = useRef<HTMLDivElement>(null);
	const [fit, setFit] = useState({key: -1, k: 1});
	// the Arabic font arrives after the first layout: measure again once it has loaded
	const [fontsReady, setFontsReady] = useState(false);
	useEffect(() => {
		const handle = delayRender('caption fonts');
		// fonts load lazily (and per unicode subset), so ask for the Arabic glyphs explicitly
		const load = (f: string) => document.fonts.load(`700 64px ${f}`, 'فالمقاولة').catch(() => []);
		Promise.all([load("'Thmanyah Sans'"), load("'Cairo'")]).then(() => {
			setFontsReady(true);
			requestAnimationFrame(() => continueRender(handle));
		});
	}, []);
	const k = g && fit.key === g.start ? fit.k : 1;
	useLayoutEffect(() => {
		const row = rowRef.current;
		if (!g || !row) return;
		const kids = Array.from(row.children) as HTMLElement[];
		const gap = parseFloat(getComputedStyle(row).columnGap) || 0;
		const w = kids.reduce((n, el) => n + el.offsetWidth, 0) + gap * Math.max(kids.length - 1, 0);
		const want = Math.min(1, (MAX_W * k) / w);
		if (fontsReady && (fit.key !== g.start || Math.abs(want - k) > 0.005)) setFit({key: g.start, k: want});
	});
	if (!g) return null;
	const ws = g.words.map((i) => words[i]);
	const gFrame = Math.round(g.start * fps);
	const pop = spring({frame: frame - gFrame, fps, config: {damping: 12, stiffness: 220, mass: 0.7}});
	const scale = 0.82 + 0.18 * pop;

	const chars = ws.reduce((n, w) => n + [...w.w].length, 0);
	const gaps = Math.max(ws.length - 1, 0);
	const fontSize = Math.min(92, MAX_W / (chars * 0.5 + gaps * 0.25)) * k;

	// active word = the last word whose start has passed
	let active = -1;
	ws.forEach((w, i) => {
		if (t >= w.start) active = i;
	});

	return (
		<div style={{position: 'absolute', top: TOP, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
			<div style={{transform: `scale(${scale})`, transformOrigin: '50% 0%'}}>
				<Glass tone="dark" radius={40} sheenFrom={gFrame} style={{padding: '14px 34px 20px', maxWidth: MAX_W + 68}}>
					<div ref={rowRef} style={{display: 'flex', flexDirection: 'row-reverse', gap: fontSize * 0.28, alignItems: 'baseline', justifyContent: 'center'}}>
						{ws.map((w, i) => {
							const isActive = i === active;
							const spoken = i <= active;
							const bump = isActive ? spring({frame: frame - Math.round(w.start * fps), fps, config: {damping: 10, stiffness: 260}}) : 0;
							return (
								<span
									key={i}
									style={{
										fontFamily: AR_FONT,
										fontWeight: 700,
										fontSize,
										lineHeight: 1.35,
										direction: 'rtl',
										whiteSpace: 'nowrap',
										flexShrink: 0,
										color: isActive ? BRAND.gold : BRAND.white,
										textShadow: isActive ? goldCrystal : whiteCrystal,
										opacity: spoken ? 1 : 0.55,
										display: 'inline-block',
										transform: `scale(${1 + 0.1 * bump})`,
									}}
								>
									{w.w}
								</span>
							);
						})}
					</div>
				</Glass>
			</div>
			{g.en ? (
				<div style={{marginTop: 14, transform: `scale(${scale})`, transformOrigin: '50% 0%'}}>
					<Glass tone="dark" radius={24} style={{padding: '8px 22px', maxWidth: MAX_W + 44}}>
						<div style={{fontFamily: EN_FONT, fontWeight: 800, fontSize: 34, color: BRAND.white, textAlign: 'center', letterSpacing: 0.5, lineHeight: 1.2}}>
							<EnLine text={g.en} />
						</div>
					</Glass>
				</div>
			) : null}
		</div>
	);
};
