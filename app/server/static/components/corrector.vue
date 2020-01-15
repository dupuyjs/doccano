<template lang="pug">
    div.card
        header.card-header
            div.card-header-title.has-background-royalblue.is-block
              div#waveform
                div.spin(v-if="loading")
                  i.fa.fa-spinner.fa-pulse.fa-3x.fa-fw
              div.controls.columns
                div.column.is-3
                div.column.is-1
                  a.button(v-on:click="replay()")
                    span.icon.tooltip(data-tooltip="Replay")
                      i.fas.fa-redo
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
        header.card-header(v-if="doc.isValidated")
            div.card-header-title.has-background-royalblue
              div.field.is-grouped.is-grouped-multiline
                div.control(v-for="label in labels")
                  div.tags.has-addons
                    a.tag.is-medium(
                      v-shortkey.once="replaceNull(shortcutKey(label))"
                      v-bind:style="{ \
                        color: label.text_color, \
                        backgroundColor: label.background_color \
                      }"
                      v-on:click="annotate(label.id)"
                      v-on:shortkey="annotate(label.id)"
                    ) {{ label.text }}
                    span.tag.is-medium
                      kbd {{ shortcutKey(label) | simpleShortcut }}
        div.card-content
          header.header(v-if="!doc.isValidated")
            div.columns(v-if="doc.isIgnored")
              div.column
                div.notification.is-warning This document was
                  strong  ignored
                  a.button.is-success.is-pulled-right(@click="ignoreDocument")
                    span.icon
                      i.fas.fa-history
                    span Restore document
            div.columns
              div.column
                textarea.textarea.is-medium(
                  type="text"
                  v-model="correctedText"
                  :disabled="doc.isIgnored"
                  placeholder="Correct audio transcript here ..."
                  autofocus
                )
            div.columns(v-if="!doc.isIgnored")
              div.column
                div.buttons.is-right
                  a.button.is-danger(@click="revertOriginal")
                    span.icon
                      i.fas.fa-history
                    span Revert to original
                  a.button.is-warning(@click="ignoreDocument")
                    span.icon
                      i.fas.fa-trash-alt
                    span Ignore
                  a.button.is-success(@click="approveDocumentCorrection")
                    span.icon
                      i.fas.fa-check
                    span Save

          div(v-if="doc.isValidated")
            div.columns
              div.column
                div.content(ref="textbox")
                  annotator(
                    v-bind:labels="labels"
                    v-bind:entity-positions="entityPositions"
                    v-bind:search-query="searchQuery"
                    v-bind:text="correctedText"
                    v-on:remove-label="removeLabel"
                    v-on:add-label="addLabel"
                    ref="annotator"
                  )
            div.columns
              div.column
                div.buttons.is-right
                  a.button.is-warning(@click="approveDocumentCorrection")
                    span.icon
                      i.fas.fa-edit
                    span Edit
                  a.button.is-success(@click="approveDocumentAnnotations" v-if="!doc.annotation_approver")
                    span.icon
                      i.fas.fa-check
                    span Approve annotations
                  a.button.is-danger(@click="approveDocumentAnnotations" v-else)
                    span.icon
                      i.fas.fa-ban
                    span Reject annotations

</template>

<style scoped>
.p-b-md {
  padding-bottom: 40px;
}
.is-block {
  display: block;
}
#waveform {
  width: 100%;
  background: white;
  border-radius: 40px;
  display: block;
  margin: 0 auto;
  overflow: hidden;
}
.spin {
  color: black;
  margin-left: -30px;
  width: 60px;
  margin-top: 10px;
  position: absolute;
  left: 50%;
}
.fa.fa-spinner.fa-pulse.fa-3x.fa-fw {
  color: black;
}
.controls {
  margin-top: 5px;
}
</style>

<script>
import WaveSurfer from 'wavesurfer.js';
import * as Diff from 'diff';
import RegionPlugin from 'wavesurfer.js/dist/plugin/wavesurfer.regions';
import Annotator from './annotator.vue';
import annotationMixin from './annotationMixin';
import { simpleShortcut } from './filter';

export default {
  props: ['text', 'audioFile', 'start', 'end', 'labels', 'searchQuery', 'entityPositions', 'doc'],
  data: () => ({
    correctedText: '',
    audioPlayer: null,
    isPlaying: false,
    loading: false,
  }),
  filters: { simpleShortcut },
  components: { Annotator },
  mixins: [annotationMixin],
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
    this.loading = true;
    this.audioPlayer.load(this.audioFile);
    this.audioPlayer.on('ready', () => {
      const duration = this.audioPlayer.getDuration();
      const offset = this.start / duration;
      this.audioPlayer.seekAndCenter(offset);
      this.loading = false;
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
    annotate(labelId) {
      this.$refs.annotator.addLabel(labelId);
    },
    revertOriginal() {
      this.correctedText = this.doc.machineTranscription;
    },
    playSentence() {
      if (!this.audioPlayer.isPlaying()) {
        this.isPlaying = true;
        if (this.audioPlayer.getCurrentTime() === this.start) {
          this.audioPlayer.play(this.start, this.end);
        } else if (this.audioPlayer.getCurrentTime() < this.end) {
          this.audioPlayer.play(this.audioPlayer.getCurrentTime(), this.end);
        } else {
          this.audioPlayer.play();
        }
      } else {
        this.isPlaying = false;
        this.audioPlayer.pause();
      }
    },
    replay() {
      this.isPlaying = true;
      this.audioPlayer.play(this.start, this.end);
    },
    getText() {
      return this.correctedText;
    },
    updateAnnotations() {
      const diffs = Diff.diffChars(this.text, this.correctedText, { ignoreCase: true });
      if (diffs.length > 1) {
        let currentIndex = 0;
        // eslint-disable-next-line no-restricted-syntax
        for (const diff of diffs) {
          if (diff.count === this.text.length) {
            continue;
          }
          if (diff.added) {
            // eslint-disable-next-line no-loop-func
            this.entityPositions.forEach((entity) => {
              if (entity.start_offset >= currentIndex) {
                entity.start_offset += diff.count;
                entity.end_offset += diff.count;
              } else if (entity.start_offset < currentIndex && currentIndex <= entity.end_offset) {
                entity.end_offset += diff.count;
              }
            });
          } else if (diff.removed) {
            // eslint-disable-next-line no-loop-func
            this.entityPositions.forEach((entity) => {
              if (entity.start_offset >= currentIndex) {
                entity.start_offset -= diff.count;
                entity.end_offset -= diff.count;
              } else if (entity.start_offset < currentIndex && currentIndex <= entity.end_offset) {
                entity.end_offset -= diff.count;
              }
            });
          }
          currentIndex += diff.count;

          // Emit update event
          this.entityPositions.forEach(el => this.$emit('update-label', el));
        }
      }
    },
    ignoreDocument() {
      this.$emit('ignore-document');
    },
    approveDocumentCorrection() {
      this.updateAnnotations();
      this.$emit('approve-document-correction');
    },
    approveDocumentAnnotations() {
      this.$emit('approve-document-annotations');
    },
    addLabel(label) {
      this.$emit('add-label', label);
    },

    removeLabel(index) {
      this.$emit('remove-label', index);
    },

  },
  watch: {
    start() {
      this.audioPlayer.pause();
      this.isPlaying = false;
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
