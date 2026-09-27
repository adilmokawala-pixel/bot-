import React from 'react';
import {AbsoluteFill, Audio, Easing, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Annotations} from './Annotations';
import {Background} from './Backgrounds';
import {fontFaceCss} from './brand';
import {Captions} from './Captions';
import type {Scene, Timeline} from './types';

const PUNCH = [1.0, 1.14, 1.03, 1.0, 1.1];
const SEGMENT_PUSH = 0.035;
const PERSUADE_ZOOM = 1.22;
const PULL_BACK = 0.4;
const TRANSITION = 7;
const ORIGIN = '50% 38%';

const easeInOut = Easing.inOut(Easing.cubic);
const easeOut = Easing.out(Easing.cubic);

/** Camera zoom multiplier (relative to the scene's base) at time t. */
const cameraZoom = (tl: Timeline, t: number) => {
	const segIdx = Math.max(0, tl.segments.findIndex((s) => t >= s.start && t < s.end));
	const seg = tl.segments[segIdx] ?? {start: 0, end: 1};
	const inSeg = (t - seg.start) / Math.max(seg.end - seg.start, 0.001);
	const jump = PUNCH[segIdx % PUNCH.length] * (1 + SEGMENT_PUSH * Math.min(Math.max(inSeg, 0), 1));

	const push = tl.pushes.find((p) => t >= p.start && t < p.end);
	if (!push) return jump;
	// persuasion push: no alternation inside the sentence
	const target = PERSUADE_ZOOM / 1.08;
	const holdEnd = push.end - PULL_BACK;
	if (t < holdEnd) {
		const p = (t - push.start) / Math.max(holdEnd - push.start, 0.001);
		return 1 + (target - 1) * easeInOut(Math.min(Math.max(p, 0), 1));
	}
	const q = (t - holdEnd) / PULL_BACK;
	return target + (1 - target) * easeOut(Math.min(Math.max(q, 0), 1));
};

const SceneLayer: React.FC<{tl: Timeline; scene: Scene; startFrame: number; zoom: number}> = ({tl, scene, startFrame, zoom}) => {
	const changed = scene.bg !== 'original';
	const base = changed ? 0.9 : 1.08;
	const scale = base * zoom;
	// original scene: never shift further than the zoom allows, so no black strip shows at the top
	const ty = changed ? 170 : Math.min(70, Math.max(0, (scale - 1) * 0.38 * 1920));
	const transform = `translateY(${ty}px) scale(${scale})`;
	const fill: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover'};
	if (!changed) {
		return (
			<AbsoluteFill style={{transform, transformOrigin: ORIGIN}}>
				<OffthreadVideo src={staticFile(tl.video.src)} muted style={fill} />
			</AbsoluteFill>
		);
	}
	return (
		<AbsoluteFill>
			<Background scene={scene} startFrame={startFrame} />
			<AbsoluteFill style={{transform, transformOrigin: ORIGIN, filter: 'drop-shadow(0 30px 50px rgba(0,0,0,.35))'}}>
				<OffthreadVideo src={staticFile(tl.video.alpha)} transparent muted style={fill} />
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

export const Reel: React.FC<{timeline: Timeline}> = ({timeline: tl}) => {
	const frame = useCurrentFrame();
	const {fps, durationInFrames} = useVideoConfig();
	const t = frame / fps;
	const zoom = cameraZoom(tl, t);

	const idx = Math.max(0, tl.scenes.findIndex((s) => t >= s.start && t < s.end));
	const scene = tl.scenes[idx];
	const sceneStart = Math.round(scene.start * fps);
	const inTransition = idx > 0 && frame - sceneStart < TRANSITION;
	const tp = (frame - sceneStart) / TRANSITION;

	const musicFade = Math.round(fps * 1.2);

	return (
		<AbsoluteFill style={{background: '#000'}}>
			<style>{fontFaceCss}</style>
			{inTransition ? (
				<SceneLayer tl={tl} scene={tl.scenes[idx - 1]} startFrame={Math.round(tl.scenes[idx - 1].start * fps)} zoom={zoom} />
			) : null}
			<AbsoluteFill
				style={
					inTransition
						? {
								clipPath: `circle(${interpolate(tp, [0, 1], [0, 120], {easing: easeOut})}% at 50% 42%)`,
								transform: `scale(${interpolate(tp, [0, 1], [1.08, 1])})`,
							}
						: undefined
				}
			>
				<SceneLayer tl={tl} scene={scene} startFrame={sceneStart} zoom={zoom} />
			</AbsoluteFill>
			{inTransition ? <AbsoluteFill style={{background: '#fff', opacity: 0.4 * (1 - tp)}} /> : null}

			<Annotations items={tl.annotations} />
			<Captions groups={tl.captions} words={tl.words} />

			<Audio src={staticFile(tl.voice)} />
			<Audio
				src={staticFile(tl.music.src)}
				loop
				volume={(f) =>
					tl.music.volume *
					interpolate(f, [0, musicFade, durationInFrames - musicFade, durationInFrames], [0, 1, 1, 0], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
					})
				}
			/>
			{tl.sfx.map((s, i) => (
				<Sequence key={i} from={Math.max(0, Math.round(s.at * fps))} layout="none">
					<Audio src={staticFile(`sfx/${s.name}.wav`)} volume={s.volume} />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
