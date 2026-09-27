import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AR_FONT, BRAND, EN_FONT} from './brand';
import {Glass} from './Glass';
import type {Annotation} from './types';

const BAND_TOP = 200;
const BAND_H = 220;
const EXIT = 5;

const Logo: React.FC<{size: number}> = ({size}) => (
	<div
		style={{
			width: size,
			height: size,
			borderRadius: size * 0.24,
			background: BRAND.orange,
			color: BRAND.white,
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'center',
			fontFamily: AR_FONT,
			fontWeight: 800,
			fontSize: size * 0.62,
			lineHeight: 1,
			boxShadow: 'inset 0 2px 0 rgba(255,255,255,0.35)',
		}}
	>
		م
	</div>
);

const arText = (size: number, color: string = BRAND.white): React.CSSProperties => ({
	fontFamily: AR_FONT,
	fontWeight: 700,
	fontSize: size,
	color,
	direction: 'rtl',
	whiteSpace: 'nowrap',
	lineHeight: 1.3,
	textShadow: '0 2px 10px rgba(0,0,0,0.35)',
});

const Chip: React.FC<{text: string; emoji: string; sheenFrom: number; size?: number; style?: React.CSSProperties}> = ({text, emoji, sheenFrom, size = 54, style}) => (
	<Glass tone="light" radius={36} sheenFrom={sheenFrom} style={{padding: '16px 32px', display: 'flex', alignItems: 'center', gap: 16, flexDirection: 'row-reverse', ...style}}>
		<span style={{fontSize: size * 0.95}}>{emoji}</span>
		<span style={arText(size)}>{text}</span>
	</Glass>
);

/** pop-in scale for a child that appears at `at` frames */
const usePop = (at: number) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - at, fps, config: {damping: 12, stiffness: 200}});
};

const Staggered: React.FC<{at: number; children: React.ReactNode}> = ({at, children}) => {
	const s = usePop(at);
	return <div style={{transform: `scale(${0.6 + 0.4 * s})`, opacity: Math.min(1, s * 1.4)}}>{children}</div>;
};

const Body: React.FC<{a: Annotation; f0: number}> = ({a, f0}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const t = frame / fps;
	switch (a.type) {
		case 'chip':
			return <Chip text={a.text} emoji={a.emoji} sheenFrom={f0 + 3} />;
		case 'chips2':
			return (
				<div style={{display: 'flex', flexDirection: 'row-reverse', gap: 22}}>
					{a.items.map((it, i) => (
						<Staggered key={i} at={f0 + i * 6}>
							<Chip text={it.text} emoji={it.emoji} sheenFrom={f0 + 3 + i * 6} size={48} />
						</Staggered>
					))}
				</div>
			);
		case 'comment': {
			const chars = [...a.text];
			const n = Math.round(interpolate(t, [a.typeStart, a.typeEnd], [0, chars.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
			const heartAt = Math.round(a.typeEnd * fps);
			const heart = spring({frame: frame - heartAt, fps, config: {damping: 8, stiffness: 240}});
			const caret = Math.floor(frame / 8) % 2 === 0 && n < chars.length;
			return (
				<Glass tone="light" radius={32} sheenFrom={f0 + 3} style={{padding: '18px 26px', width: 860, display: 'flex', alignItems: 'center', gap: 18, flexDirection: 'row-reverse'}}>
					<Logo size={74} />
					<div style={{flex: 1, textAlign: 'right'}}>
						<div style={{...arText(30, 'rgba(255,255,255,0.8)')}}>أضف تعليقاً…</div>
						<div style={{...arText(52), fontFamily: `${EN_FONT}, ${AR_FONT}`, fontWeight: 800, direction: 'ltr', textAlign: 'right'}}>
							{chars.slice(0, n).join('')}
							<span style={{opacity: caret ? 1 : 0}}>|</span>
						</div>
					</div>
					<span style={{fontSize: 58, transform: `scale(${heart})`, display: 'inline-block'}}>❤️</span>
				</Glass>
			);
		}
		case 'dm': {
			const second = Math.round(f0 + fps * 0.6);
			return (
				<Glass tone="light" radius={34} sheenFrom={f0 + 3} style={{padding: '20px 26px', width: 860, display: 'flex', alignItems: 'center', gap: 20, flexDirection: 'row-reverse'}}>
					<Logo size={96} />
					<div style={{flex: 1, textAlign: 'right'}}>
						<div style={arText(44)}>رسالة جديدة 📩</div>
						<Staggered at={second}>
							<div style={{...arText(40, BRAND.gold), transformOrigin: '100% 50%'}}>🔗 هاهو الرابط</div>
						</Staggered>
					</div>
				</Glass>
			);
		}
		case 'checklist':
			return (
				<div style={{display: 'flex', flexDirection: 'row-reverse', gap: 16, flexWrap: 'wrap', justifyContent: 'center', maxWidth: 1000}}>
					{a.items.map((it, i) => (
						<Staggered key={i} at={f0 + Math.round(i * 0.25 * fps)}>
							<Glass tone="light" radius={30} style={{padding: '12px 22px', display: 'flex', gap: 12, alignItems: 'center', flexDirection: 'row-reverse'}}>
								<span
									style={{
										width: 46,
										height: 46,
										borderRadius: 23,
										background: BRAND.green,
										color: BRAND.white,
										display: 'flex',
										alignItems: 'center',
										justifyContent: 'center',
										fontSize: 32,
										fontWeight: 900,
										fontFamily: EN_FONT,
									}}
								>
									✓
								</span>
								<span style={arText(44)}>{it}</span>
							</Glass>
						</Staggered>
					))}
				</div>
			);
		case 'tiles':
			return (
				<div style={{display: 'flex', flexDirection: 'row-reverse', gap: 24}}>
					{a.items.map((it, i) => {
						const on = i === a.active;
						return (
							<Staggered key={i} at={f0 + i * 5}>
								<Glass
									tone="light"
									radius={32}
									sheenFrom={on ? f0 + 8 : undefined}
									style={{
										width: 400,
										padding: '20px 18px',
										textAlign: 'center',
										opacity: on ? 1 : 0.45,
										border: on ? `4px solid ${BRAND.gold}` : '2px solid rgba(255,255,255,0.4)',
										boxShadow: on ? `0 0 30px rgba(255,212,71,0.45), inset 0 2px 0 rgba(255,255,255,0.55)` : undefined,
									}}
								>
									<div style={{fontSize: 60}}>{it.emoji}</div>
									<div style={{...arText(46), whiteSpace: 'normal'}}>{it.text}</div>
								</Glass>
							</Staggered>
						);
					})}
				</div>
			);
		case 'card':
			return (
				<Glass tone="light" radius={34} sheenFrom={f0 + 3} style={{padding: 16, width: 900, height: 200, display: 'flex', alignItems: 'center', gap: 22, flexDirection: 'row-reverse'}}>
					<div
						style={{
							width: 168,
							height: 168,
							borderRadius: 26,
							overflow: 'hidden',
							flexShrink: 0,
							background: `linear-gradient(160deg, ${BRAND.orangeLight}, ${BRAND.orangeDark})`,
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							fontSize: 96,
						}}
					>
						{a.image ? <Img src={staticFile(a.image)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : a.emoji}
					</div>
					<div style={{flex: 1, textAlign: 'right'}}>
						<div style={{...arText(52), whiteSpace: 'normal'}}>{a.title}</div>
						{a.sub ? <div style={{...arText(36, 'rgba(255,255,255,0.85)'), whiteSpace: 'normal'}}>{a.sub}</div> : null}
					</div>
				</Glass>
			);
		case 'cta': {
			const pulse = 0.5 + 0.5 * Math.sin((frame - f0) / 5);
			return (
				<div
					style={{
						position: 'relative',
						padding: '22px 44px',
						borderRadius: 999,
						background: 'rgba(242,90,36,0.55)',
						backdropFilter: 'blur(22px) saturate(170%)',
						border: `4px solid ${BRAND.gold}`,
						boxShadow: `0 0 ${18 + pulse * 26}px rgba(255,212,71,${0.35 + pulse * 0.4}), inset 0 2px 0 rgba(255,255,255,0.45), 0 18px 40px rgba(0,0,0,0.3)`,
						transform: `scale(${1 + pulse * 0.03})`,
					}}
				>
					<span style={{...arText(58), fontWeight: 800}}>{a.text}</span>
				</div>
			);
		}
	}
};

export const Annotations: React.FC<{items: Annotation[]}> = ({items}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return (
		<>
			{items.map((a, i) => {
				const f0 = Math.round(a.start * fps);
				const f1 = Math.round(a.end * fps);
				if (frame < f0 || frame >= f1) return null;
				const enter = spring({frame: frame - f0, fps, config: {damping: 12, stiffness: 200}});
				const exit = interpolate(frame, [f1 - EXIT, f1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
				const scale = (0.6 + 0.4 * enter) * (0.85 + 0.15 * exit);
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							top: BAND_TOP,
							height: BAND_H,
							left: 0,
							right: 0,
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							transform: `scale(${scale})`,
							opacity: Math.min(1, enter * 1.5) * exit,
						}}
					>
						<Body a={a} f0={f0} />
					</div>
				);
			})}
		</>
	);
};
