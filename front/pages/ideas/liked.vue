<template>
  <ideas-list-page
    :initial-ideas="ideas"
    :initial-next-token="nextToken"
    title="SAVED IDEAS"
    :end-point="endPoint"
    :end-point-name="endPointName"
    show-author
  ></ideas-list-page>
</template>

<script>
import getLikedIdeas from '~/graphql/query/getLikedIdeas'
import ideasListPage from '@/components/ideasList/ideasListPage'
import loadIdeas from '@/components/ideasList/loadIdeas'

export default {
  components: { ideasListPage },
  middleware: 'authenticated',
  asyncData({ app, store }) {
    return loadIdeas(app.$amplifyApi, 'getLikedIdeas', getLikedIdeas)
  },
  data() {
    return {
      endPoint: getLikedIdeas,
      endPointName: 'getLikedIdeas'
    }
  }
}
</script>
