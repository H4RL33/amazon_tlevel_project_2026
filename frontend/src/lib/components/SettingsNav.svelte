<!--
  SettingsNav
  Purpose: Vertical nav, adapted from NavSidebar, for the Account Settings / App Settings pages
    reachable from the NavBarAvatar dropdown.
  Used in: /settings
  Props:
    - activePath (string): current URL path — highlight the matching link
  Layout:
    "Account" section: Profile, Email & Password.
    "App" section: Notifications, Accessibility (TODO: confirm exact sub-pages with the team).
  Styling:
    Same visual language as NavSidebar (background #0a2540, width 240px), section labels in
    muted uppercase text above each group.
-->
<script lang="ts">
  export let activePath: string;
</script>

<!-- TODO: Implement the two link sections above, highlighting the one matching activePath. -->
