import React from 'react';
import {Composition, staticFile} from 'remotion';
import {Reel} from './Reel';
import type {Timeline} from './types';

type Props = {id: string; timeline?: Timeline};

export const Root: React.FC = () => (
	<Composition
		id="Reel"
		component={({timeline}: Props) => <Reel timeline={timeline as Timeline} />}
		width={1080}
		height={1920}
		fps={30}
		durationInFrames={300}
		defaultProps={{id: 'source'} as Props}
		calculateMetadata={async ({props}) => {
			const res = await fetch(staticFile(`${props.id}/timeline.json`));
			const timeline = (await res.json()) as Timeline;
			return {durationInFrames: timeline.durationInFrames, fps: timeline.fps, props: {...props, timeline}};
		}}
	/>
);
