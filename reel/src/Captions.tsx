import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {AR_FONT, BRAND, EN_FONT} from './brand';
import {Glass} from './Glass';
import type {CaptionGroup, Word} from './types';

const TOP = 1560;

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
	if (!g) return null;
	const ws = g.words.map((i) => words[i]);
	const gFrame = Math.round(g.start * fps);
	const pop = spring({frame: frame - gFrame, fps, config: {damping: 12, stiffness: 220, mass: 0.7}});
	const scale = 0.82 + 0.18 * pop;

	const chars = ws.reduce((n, w) => n + [...w.w].length, 0);
	const gaps = Math.max(ws.length - 1, 0);
	const fontSize = Math.min(104, 880 / (chars * 0.5 + gaps * 0.25));

	// active word = the last word whose start has passed
	let active = -1;
	ws.forEach((w, i) => {
		if (t >= w.start) active = i;
	});

	return (
		<div style={{position: 'absolute', top: TOP, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
			<div style={{transform: `scale(${scale})`, transformOrigin: '50% 0%'}}>
				<Glass tone="dark" radius={40} sheenFrom={gFrame} style={{padding: '18px 38px 26px', maxWidth: 1000}}>
					<div style={{display: 'flex', flexDirection: 'row-reverse', gap: fontSize * 0.28, alignItems: 'baseline', justifyContent: 'center'}}>
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
					<Glass tone="dark" radius={24} style={{padding: '10px 24px', maxWidth: 1000}}>
						<div style={{fontFamily: EN_FONT, fontWeight: 800, fontSize: 38, color: BRAND.white, textAlign: 'center', letterSpacing: 0.5, lineHeight: 1.2}}>
							<EnLine text={g.en} />
						</div>
					</Glass>
				</div>
			) : null}
		</div>
	);
};
