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
  // Code is incomplete and is currently using filler variables, needs updating.
  // Changes --------------------------------------------->
  // Template -------------------------------------------->


  // Receives the current URL path from the parent component.
  // Used to determine which navigation link should be highlighted.
  export let activePath: string;
   
  // Array of links displayed under the "Account" section.
  // Each object should contain a display name and the page path.
  const account_links = [...]

  // Array of links displayed under the "App" section.
  // Each object should contain a display name and the page path.
  const app_links = [...]

</script>

<!-- Settings navigation sidebar -->
<nav>

  <!-- Account settings section heading -->
  <h3>Account</h3>

  <!-- Loop through each account settings link -->
  {#each account_links as link}
    <a
      href={link.path}
      class:active={activePath === link.path}
    >
      {link.name}
    </a>
  {/each}

  <!-- Loop through each application settings link -->
  {#each app_links as link}
    <a
      href={link.path}
      class:active={activePath === link.path}
    >
      {link.name}
    </a>
  {/each}
</nav>

<style>
  /* Styles the sidebar container */
  nav {
    width: 240px;
    background: #0a2540;
    display: flex;
    flex-direction: column;
    padding: 1rem;
  }

  /* Styles the section headings (e.g. Account, App) */
  h3 {
    color: #8ca0b3;
    text-transform: uppercase;
    font-size: 0.75rem;
    margin: 1rem 0 0.5rem;
  }

  /* Default appearance of navigation links */
  a {
    color: white;
    text-decoration: none;
    padding: 0.75rem;
    border-radius: 6px;
  }

  /* Applied to the link whose path matches activePath */
  a.active {
    background: #173b61;
    font-weight: bold;
  }
</style>

<!-- Template ----------------------------------------------> 
<!-- Changes -----------------------------------------------> 
<!-- Code is incomplete and is currently using filler variables, needs updating. -->