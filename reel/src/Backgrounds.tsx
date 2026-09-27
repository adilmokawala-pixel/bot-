import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {AR_FONT, BRAND, EN_FONT} from './brand';
import {Glass, GlassSquare} from './Glass';
import type {Scene} from './types';

const W = 1080;
const H = 1920;

/** deterministic pseudo-random */
const rnd = (i: number) => {
	const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
	return x - Math.floor(x);
};

const OrangeBg: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
	const squares = Array.from({length: 7}, (_, i) => i);
	const slide = interpolate(local, [0, 150], [260, -260]);
	return (
		<AbsoluteFill style={{background: `linear-gradient(160deg, ${BRAND.orangeLight} 0%, ${BRAND.orange} 48%, ${BRAND.orangeDark} 100%)`}}>
			{squares.map((i) => {
				const size = 120 + rnd(i) * 150;
				const x = rnd(i + 10) * W;
				const y = 180 + rnd(i + 20) * (H - 360);
				const drift = Math.sin((local + i * 23) / 55) * 22;
				return <GlassSquare key={i} size={size} x={x + drift} y={y - local * (0.25 + rnd(i) * 0.3)} rot={rnd(i + 5) * 30 - 15 + local * 0.05} />;
			})}
			{scene.keyword ? (
				<div
					style={{
						position: 'absolute',
						top: 520,
						left: 0,
						right: 0,
						textAlign: 'center',
						whiteSpace: 'nowrap',
						transform: `translateX(${slide}px)`,
						fontFamily: `${EN_FONT}, ${AR_FONT}`,
						fontWeight: 900,
						fontSize: 330,
						lineHeight: 1,
						color: 'rgba(255,255,255,0.13)',
						letterSpacing: -6,
					}}
				>
					{scene.keyword}
				</div>
			) : null}
		</AbsoluteFill>
	);
};

const DEFAULT_ICONS = ['💰', '📄', '🏦', '📈', '🤝'];

const DarkBg: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
	const icons = scene.icons?.length ? scene.icons : DEFAULT_ICONS;
	const spots = [
		{x: 150, y: 600, s: 170, blur: 0},
		{x: 930, y: 540, s: 150, blur: 4},
		{x: 120, y: 1120, s: 130, blur: 7},
		{x: 960, y: 1020, s: 180, blur: 0},
		{x: 540, y: 470, s: 100, blur: 10},
	];
	const gridShift = local * 0.6;
	return (
		<AbsoluteFill style={{background: BRAND.dark}}>
			<AbsoluteFill
				style={{
					backgroundImage:
						'linear-gradient(rgba(255,255,255,0.05) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.05) 2px, transparent 2px)',
					backgroundSize: '90px 90px',
					backgroundPosition: `0 ${gridShift}px`,
				}}
			/>
			<AbsoluteFill
				style={{background: 'radial-gradient(circle at 50% 42%, rgba(242,90,36,0.55) 0%, rgba(242,90,36,0.18) 26%, rgba(14,13,12,0) 55%)'}}
			/>
			{spots.map((p, i) => (
				<GlassSquare
					key={i}
					size={p.s}
					x={p.x + Math.sin((local + i * 30) / 40) * 12}
					y={p.y + Math.cos((local + i * 17) / 45) * 14}
					rot={Math.sin((local + i * 11) / 60) * 8}
					blur={p.blur}
				>
					{icons[i % icons.length]}
				</GlassSquare>
			))}
		</AbsoluteFill>
	);
};

/** Path nodes: alternate sides, clear of the annotation band and of Instagram's right-hand buttons (x>=960, y>=1000). */
const PATH_NODES = [
	{x: 170, y: 560},
	{x: 900, y: 720},
	{x: 170, y: 870},
	{x: 900, y: 975},
];
const pathLabels = (scene: Scene) => (scene.path?.length ? scene.path : ['الفكرة', 'الملف', 'التمويل', 'المشروع']);
const drawFrames = (fps: number) => Math.round(fps * 2.2);

const LightBg: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
	const {fps} = useVideoConfig();
	const nodes = PATH_NODES.slice(0, pathLabels(scene).length);
	const d = nodes.reduce((acc, n, i) => {
		if (i === 0) return `M ${n.x} ${n.y}`;
		const p = nodes[i - 1];
		const my = (p.y + n.y) / 2;
		return `${acc} C ${p.x} ${my}, ${n.x} ${my}, ${n.x} ${n.y}`;
	}, '');
	const progress = interpolate(local, [4, drawFrames(fps)], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: Easing.inOut(Easing.cubic),
	});
	const LEN = 3000;
	return (
		<AbsoluteFill style={{background: BRAND.cream}}>
			<AbsoluteFill
				style={{backgroundImage: 'radial-gradient(rgba(14,13,12,0.16) 3px, transparent 3px)', backgroundSize: '44px 44px'}}
			/>
			<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
				<path d={d} fill="none" stroke={BRAND.orange} strokeWidth={10} strokeLinecap="round" strokeDasharray={LEN} strokeDashoffset={LEN * (1 - progress)} pathLength={LEN} />
			</svg>
		</AbsoluteFill>
	);
};

/** Path labels sit in front of the person so the head never hides them. */
const LightLabels: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
	const {fps} = useVideoConfig();
	const labels = pathLabels(scene);
	const nodes = PATH_NODES.slice(0, labels.length);
	const dd = drawFrames(fps);
	return (
		<AbsoluteFill>
			{nodes.map((n, i) => {
				const at = 4 + (dd - 4) * (i / Math.max(nodes.length - 1, 1));
				const s = spring({frame: local - at, fps, config: {damping: 13, stiffness: 180}});
				return (
					<div key={i} style={{position: 'absolute', left: n.x, top: n.y, transform: `translate(-50%,-50%) scale(${0.6 + 0.4 * s})`, opacity: s}}>
						<Glass tone="light" radius={28} style={{padding: '12px 24px', background: 'rgba(255,255,255,0.72)', border: `3px solid ${BRAND.orange}`}}>
							<span style={{fontFamily: AR_FONT, fontWeight: 700, fontSize: 42, color: BRAND.dark, direction: 'rtl', whiteSpace: 'nowrap'}}>{labels[i]}</span>
						</Glass>
					</div>
				);
			})}
		</AbsoluteFill>
	);
};

/** Scene elements drawn above the person layer. */
export const Foreground: React.FC<{scene: Scene; startFrame: number}> = ({scene, startFrame}) => {
	const frame = useCurrentFrame();
	if (scene.bg === 'light') return <LightLabels scene={scene} local={frame - startFrame} />;
	return null;
};

/** Illustration picture behind the person: slow Ken Burns + brand-tinted vignette. */
const ImageBg: React.FC<{scene: Scene; local: number}> = ({scene, local}) => {
	const {fps} = useVideoConfig();
	const zoom = 1.06 + local * 0.0009;
	const s = spring({frame: local - 6, fps, config: {damping: 14, stiffness: 160}});
	return (
		<AbsoluteFill style={{background: BRAND.dark}}>
			{scene.image ? (
				<Img src={staticFile(scene.image)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${zoom})`}} />
			) : null}
			<AbsoluteFill
				style={{
					background:
						'linear-gradient(180deg, rgba(14,13,12,0.55) 0%, rgba(14,13,12,0) 30%, rgba(14,13,12,0) 60%, rgba(14,13,12,0.7) 100%), radial-gradient(circle at 50% 45%, rgba(242,90,36,0) 35%, rgba(169,51,9,0.35) 100%)',
				}}
			/>
			{scene.label ? (
				<div style={{position: 'absolute', top: 470, right: 50, transform: `scale(${0.6 + 0.4 * s})`, opacity: s, transformOrigin: '100% 50%'}}>
					<Glass tone="dark" radius={26} style={{padding: '12px 26px', border: `3px solid ${BRAND.orange}`}}>
						<span style={{fontFamily: AR_FONT, fontWeight: 700, fontSize: 44, color: BRAND.white, direction: 'rtl', whiteSpace: 'nowrap'}}>{scene.label}</span>
					</Glass>
				</div>
			) : null}
		</AbsoluteFill>
	);
};

export const Background: React.FC<{scene: Scene; startFrame: number}> = ({scene, startFrame}) => {
	const frame = useCurrentFrame();
	const local = frame - startFrame;
	if (scene.bg === 'orange') return <OrangeBg scene={scene} local={local} />;
	if (scene.bg === 'dark') return <DarkBg scene={scene} local={local} />;
	if (scene.bg === 'light') return <LightBg scene={scene} local={local} />;
	if (scene.bg === 'image') return <ImageBg scene={scene} local={local} />;
	return null;
};
