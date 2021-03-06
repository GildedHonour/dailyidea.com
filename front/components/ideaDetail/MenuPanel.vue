<template>
  <div class="idea-part__header__buttons-panel">
    <v-btn
      text
      icon
      :disabled="!editable"
      color="gray"
      width="48"
      height="48"
      @click="toggleIdeaPrivacy"
    >
      <img
        v-if="isPrivate"
        class=""
        height="22"
        src="~/assets/images/privateIdea.png"
      />
      <img v-else class="" height="22" src="~/assets/images/publicIdea.png" />
    </v-btn>
    <v-btn icon width="48" height="48" @click="showShareIdeaDialog">
      <v-icon>share</v-icon>
    </v-btn>
    <v-menu v-if="editable" offset-y left transition="slide-y-transition">
      <template v-slot:activator="{ on }">
        <v-btn icon width="48" height="48" v-on="on">
          <v-icon size="22">fas fa-ellipsis-v</v-icon>
        </v-btn>
      </template>
      <v-list>
        <v-list-item @click="enableEditMode">
          <v-list-item-title>
            <v-icon size="18" style="vertical-align: middle; width: 21px"
              >mdi-pencil
            </v-icon>
            <span style="vertical-align: middle">
              Edit Idea</span
            ></v-list-item-title
          >
        </v-list-item>
        <v-list-item @click="deleteIdea">
          <v-list-item-title>
            <v-icon size="18" style="vertical-align: middle; width: 21px"
              >fas fa-trash
            </v-icon>
            <span style="vertical-align: middle">
              Delete Idea</span
            ></v-list-item-title
          >
        </v-list-item>
      </v-list>
    </v-menu>
    <save-idea-bookmark
      @savedStateChanged="onIdeaSaveStateChanged"
    ></save-idea-bookmark>
    <ShareIdeaByEmailDialog
      :idea-id="$route.params.ideaId"
      :idea-owner-id="$route.params.userId"
      :visible="showEmailShareDialog"
      @success="onSharedIdeaOverEmail"
      @error="onSharedIdeaOverEmailError"
      @close="showEmailShareDialog = false"
      @onCopyShareLink="onCopyShareLink"
    ></ShareIdeaByEmailDialog>
    <make-idea-private-dialog
      ref="makeIdeaPrivateDialog"
    ></make-idea-private-dialog>
    <make-idea-public-dialog
      ref="makeIdeaPublicDialog"
    ></make-idea-public-dialog>
  </div>
</template>

<script>
import { graphqlOperation } from '@aws-amplify/api'
import makeIdeaPrivate from '~/graphql/mutations/makeIdeaPrivate'
import makeIdeaPublic from '~/graphql/mutations/makeIdeaPublic'
import ShareIdeaByEmailDialog from '@/components/dialogs/shareIdeaByEmail'
import SaveIdeaBookmark from '@/components/ideaDetail/SaveIdeaBookmark'
import makeIdeaPrivateDialog from '~/components/dialogs/makeIdeaPrivateDialog'
import makeIdeaPublicDialog from '~/components/dialogs/makeIdeaPublicDialog'

export default {
  name: 'MenuPanel',
  components: {
    SaveIdeaBookmark,
    ShareIdeaByEmailDialog,
    makeIdeaPrivateDialog,
    makeIdeaPublicDialog
  },
  props: {
    editable: {
      type: Boolean,
      default: false
    },
    idea: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      showEmailShareDialog: false
    }
  },
  computed: {
    isPrivate() {
      return this.idea.visibility === 'PRIVATE'
    }
  },
  methods: {
    deleteIdea() {
      this.$emit('onDeleteIdea')
    },
    onIdeaSaveStateChanged(val) {
      this.$emit('savedStateChanged', val)
    },
    async makeIdeaPrivate() {
      const confirmed = await this.$refs.makeIdeaPrivateDialog.show()
      if (!confirmed) {
        return
      }
      this.$store.commit('layoutState/showProgressBar')
      try {
        const ideaId = this.idea.ideaId
        const result = await this.$amplifyApi.graphql(
          graphqlOperation(makeIdeaPrivate, {
            ideaId
          })
        )
        if (result.data.makeIdeaPrivate.ok) {
          this.$emit('onIdeaVisibilityChanged', { isPrivate: true })
        } else {
          this.$emit('onIdeaVisibilityChangeError', { isPrivate: true })
        }
      } catch (err) {
        this.$emit('onIdeaVisibilityChangeError', { isPrivate: true })
      }
      this.$store.commit('layoutState/hideProgressBar')
    },
    async makeIdeaPublic() {
      const confirmed = await this.$refs.makeIdeaPublicDialog.show()
      if (!confirmed) {
        return
      }
      this.$store.commit('layoutState/showProgressBar')
      try {
        const ideaId = this.idea.ideaId
        const result = await this.$amplifyApi.graphql(
          graphqlOperation(makeIdeaPublic, {
            ideaId
          })
        )
        if (result.data.makeIdeaPublic.ok) {
          this.$emit('onIdeaVisibilityChanged', { isPrivate: false })
        } else {
          this.$emit('onIdeaVisibilityChangeError', { isPrivate: false })
        }
      } catch (err) {
        this.$emit('onIdeaVisibilityChangeError', { isPrivate: false })
      }
      this.$store.commit('layoutState/hideProgressBar')
    },
    toggleIdeaPrivacy() {
      if (this.isPrivate) {
        this.makeIdeaPublic()
      } else {
        this.makeIdeaPrivate()
      }
    },
    showShareIdeaDialog() {
      this.showEmailShareDialog = true
    },
    enableEditMode() {
      this.$emit('enableEditMode')
    },
    onSharedIdeaOverEmail() {
      this.$emit('onNotification', { type: 'success', message: 'Idea shared!' })
    },
    onSharedIdeaOverEmailError() {
      this.$emit('onNotification', {
        type: 'error',
        message: "Can't share Idea"
      })
    },
    onCopyShareLink() {
      this.$emit('onNotification', { type: 'success', message: 'Link copied' })
    }
  }
}
</script>

<style scoped lang="scss">
$base-height: 50px;
.idea-part__header__buttons-panel {
  @media (max-width: $screen-xs-max) {
  }
  @media (min-width: $screen-sm-min) {
    display: inline-block;
    float: right;
    width: 200px;
  }
  height: $base-height;
  text-align: right;
  vertical-align: top;

  /*font-size: 22px;*/
  /*background-color: #d2a7af;*/
  min-height: 50px;
}
</style>
