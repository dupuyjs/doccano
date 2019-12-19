<template lang="pug">
extends ./conversations.pug

block conversations-selection
  div
    | Please select a conversation:
    div.control
      select(v-model="selectedConversationId", name="selectedConversationId", required)
        option(v-for="c in conversations", v-bind:value="c.id") {{ parseTitle(c) }}

block annotation-area
  div.card(
      v-if="docs[pageNumber] && annotations[pageNumber] && docs[pageNumber].textValidated"
    )
      header.card-header
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
        div.content.scrollable(ref="textbox")
          annotator(
            v-bind:labels="labels"
            v-bind:entity-positions="annotations[pageNumber]"
            v-bind:search-query="searchQuery"
            v-bind:text="docs[pageNumber].text"
            v-on:remove-label="removeLabel"
            v-on:add-label="addLabel"
            ref="annotator"
          )
  
  corrector(
    v-if="docs[pageNumber] && !docs[pageNumber].textValidated"
    v-bind:text="docs[pageNumber].text"
    v-bind:audioFile="this.conversations.find(c => c.id === this.selectedConversationId).audioFile"
    ref="corrector"
  )

</template>

<style scoped>
.card-header-title {
  padding: 1.5rem;
}
</style>

<script>
import annotationMixin from './annotationMixin';
import Annotator from './annotator.vue';
import Corrector from './corrector.vue';

import HTTP from './http';
import { simpleShortcut } from './filter';

export default {

  data() {
    return {
      conversations: [],
      selectedConversationId: 0,
      correctedTranscript: ""
    };
  },

  filters: { simpleShortcut },

  components: { Annotator, Corrector },

  mixins: [annotationMixin],

  methods: {
    annotate(labelId) {
      this.$refs.annotator.addLabel(labelId);
    },

    addLabel(annotation) {
      const docId = this.docs[this.pageNumber].id;
      HTTP.post(`docs/${docId}/annotations`, annotation).then((response) => {
        this.annotations[this.pageNumber].push(response.data);
      });
    },

    async submit() {
      if (this.selectedConversationId != 0) {
        const state = this.getState();
        this.url = `docs?q=${this.searchQuery}&conversation=${this.selectedConversationId}&seq_annotations__isnull=${state}&offset=${this.offset}&ordering=${this.ordering}`;
        await this.search();
        this.pageNumber = 0;
      }
    },

    parseTitle(conversation) {
      var c = JSON.parse(conversation.metadata);
      if (c.service !== undefined)
        return c.service;
      else return `Conversation ${c.id}`;
    },

  },

  watch: {
    selectedConversationId: async function () {
      await this.submit();
    },

    docs: function() {
      Object.keys(this.docs).forEach(k => {
        // If doc is validated, display humanTranscription, else humanTranscription
        let doc = this.docs[k];
        doc.text = (doc.textValidated ? doc.humainTranscription : doc.machineTranscription);
      });      
    }
  },

  async created() {
    // Load conversations into drop down
    var response = await HTTP.get('conversations')
    this.conversations = response.data;
  }
};
</script>
