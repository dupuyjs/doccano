<template lang="pug">
    div.card.has-text-weight-bold.has-text-white.has-background-royalblue
        div.card-content
          div
            div#waveform
            div.controls.columns
              div.column.is-4
              div.column.is-1
                a.button(v-on:click="audioPlayer.skipBackward()")
                  span.icon.tooltip(data-tooltip="Backward")
                    i.fas.fa-backward
              div.column.is-1
                a.button(v-on:click="playSentence()")
                  span.icon.tooltip(data-tooltip="Play/Pause")
                    i.fas.fa-pause(v-if="isPlaying")
                    i.fas.fa-play(v-else)
              div.column.is-1
                a.button(v-on:click="audioPlayer.skipForward()")
                  span.icon.tooltip(data-tooltip="Forward")
                    i.fas.fa-forward
              div.column.is-1(v-if="audioPlayer")
                a.button(v-on:click="audioPlayer.setMute(!audioPlayer.getMute())")
                  span.icon.tooltip(data-tooltip="Volume")
                    i.fas.fa-volume-off(v-if="audioPlayer.getMute()")
                    i.fas.fa-volume-up(v-else)
              div.column.is-4
        section
          header.header
            textarea.textarea(
              type="text"
              v-model="correctedText"
              placeholder="Correct audio transcript here ..."
              autofocus
            )

</template>

<style scoped>
#waveform {
  width: 100%;
  background: white;
  border-radius: 40px;
  display: block;
  margin: 0 auto;
  overflow: hidden;
}
.controls {
  margin-top: 5px;
}
</style>

<script>
import WaveSurfer from 'wavesurfer.js';
import RegionPlugin from 'wavesurfer.js/dist/plugin/wavesurfer.regions';

export default {
  props: ['text', 'audioFile', 'start', 'end'],
  data: () => ({
    correctedText: '',
    audioPlayer: null,
    isPlaying: false,
    loading: false,
  }),
  mounted() {
    this.audioPlayer = WaveSurfer.create({
      container: '#waveform',
      waveColor: '#626262',
      progressColor: 'black',
      fillParent: false,
      height: 80,
      scrollParent: true,
      minPxPerSec: 50,
      plugins: [
        RegionPlugin.create({
          regions: [
            {
              start: this.start,
              end: this.end,
              drag: false,
              resize: false,
              loop: false,
              color: 'hsla(225, 73%, 57%, 0.3)',
            },
          ],
        }),
      ],
    });
    this.audioPlayer.load(this.audioFile);
    this.audioPlayer.on('ready', () => {
      const duration = this.audioPlayer.getDuration();
      const offset = this.start / duration;
      this.audioPlayer.seekAndCenter(offset);
    });

    this.audioPlayer.on('region-click', (region, e) => {
      e.stopPropagation();
      if (!this.audioPlayer.isPlaying()) {
        this.isPlaying = true;
        region.play();
      } else {
        this.isPlaying = false;
        this.audioPlayer.pause();
      }
    });

    this.audioPlayer.on('pause', () => {
      this.isPlaying = false;
    });

    this.audioPlayer.on('seek', () => {
      if (this.audioPlayer.isPlaying()) {
        this.isPlaying = true;
      } else {
        this.isPlaying = false;
      }
    });
  },
  methods: {
    playSentence() {
      if (!this.audioPlayer.isPlaying()) {
        this.isPlaying = true;
        if (this.audioPlayer.getCurrentTime() === this.start) {
          this.audioPlayer.play(this.start, this.end);
        } else {
          this.audioPlayer.play();
        }
      } else {
        this.isPlaying = false;
        this.audioPlayer.pause();
      }
    },
    getText() {
      return this.correctedText;
    },
  },
  watch: {
    start() {
      this.audioPlayer.clearRegions();
      this.audioPlayer.addRegion({
        start: this.start,
        end: this.end,
        drag: false,
        resize: false,
        loop: false,
        color: 'hsla(225, 73%, 57%, 0.3)',
      });

      const duration = this.audioPlayer.getDuration();
      const offset = this.start / duration;
      this.audioPlayer.seekAndCenter(offset);
    },
    text() {
      this.correctedText = this.text;
    },
  },
  created() {
    this.correctedText = this.text;
  },

};
</script>
