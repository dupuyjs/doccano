<template lang="pug">
    div.card.has-text-weight-bold.has-text-white.has-background-royalblue
        div.card-content
            div.content
                audio.audio(
                    ref="player"
                    controls
                    v-bind:src="audioFile"
                    v-shortkey="{ playOrPauseAudio: ['alt', 'p'] }"
                    v-on:shortkey="playOrPauseAudio"
                )                    
        
        section
            header.header
                textarea.textarea(
                    type="text"
                    v-model="text"
                    placeholder="Correct audio transcript here ..."
                    autofocus
                )

</template>

<style scoped>
audio {
  height: 3em;
  width: 100%;
  display: block;
  margin: 0 auto;
}
</style>

<script>
export default {
  props: {
    text: {
      type: String,
      default: '',
    },
    audioFile: {
      type: String,
      default: ''
    },
  },

  data: () => ({

  }),

  computed: {
    
  },

  watch: {

  },

  methods: {
    async playOrPauseAudio() {
      const player = this.$refs.player;
      if (this.isAudioPlaying) {
        player.pause();
        this.isAudioPlaying = false;
      } else {
        await player.play();
        this.isAudioPlaying = true;
      }
    },

  },
};
</script>
