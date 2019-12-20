<template lang="pug">
    div.card.has-text-weight-bold.has-text-white.has-background-royalblue
        div.card-content
            div.content
                audio.audio(
                    ref="player"
                    controls
                    v-shortkey="{ playOrPauseAudio: ['alt', 'p'] }"
                    v-on:shortkey="playOrPauseAudio"
                )                    
        
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
      correctedText: ''
  }),

  mounted() {
    this.$nextTick(() => {
        const player = this.$refs.player;
        player.src = this.audioFile;
        player.type = "audio/wav";
    })
  },

  methods: {
    async playOrPauseAudio() {
      const player = this.$refs.player;
      console.log(player);
      if (this.isAudioPlaying) {
        player.pause();
        this.isAudioPlaying = false;
      } else {
        await player.play();
        this.isAudioPlaying = true;
      }
    },

    getText() {
        return this.correctedText;
    }

  },

  created() {
      this.correctedText = this.text;      
  }
};
</script>
