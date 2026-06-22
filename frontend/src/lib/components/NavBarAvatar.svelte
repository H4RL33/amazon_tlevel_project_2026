<!--
  NavBarAvatar
  Purpose: User avatar shown on the right of the NavBar with a dropdown for account settings,
    app settings, their dashboard, and help.
  Used in: NavBar
  Props:
    - user (UserResponse): current user — render avatar image if available, else initials
      from first_name/last_name on a coloured circle.
  Behaviour:
    - Clicking the avatar toggles a dropdown panel anchored below-right of the avatar.
    - Dropdown items: "Dashboard" (/dashboard), "Account Settings" (/settings),
      "App Settings" (/settings), "Help" (/help).
    - Clicking outside the dropdown or pressing Escape closes it.
  Styling:
    Avatar: 36px circle, object-fit cover for images.
    Dropdown: background #161b22, border 1px solid #21262d, border-radius 8px,
    box-shadow 0 4px 12px rgba(0,0,0,0.4), min-width 180px.
-->
<script lang="ts">
  import type { UserResponse } from '$lib/api/types';

  export let user: UserResponse;

  let open = false;
</script>

<!-- TODO: Implement avatar button that toggles `open`, and a dropdown menu with the four links above. -->
<!-- TODO: Close the dropdown on outside click / Escape (use a Svelte action or window listener). -->
