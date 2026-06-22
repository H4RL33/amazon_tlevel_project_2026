<!--
  AlbumCard
  Purpose: Wide card used to open an Album — a curated, course-like set of Snippets forming a
    learning pathway. Requires an account to enrol.
  Used in: CTASidebar, AlbumGrid, EnrolledAlbumsList
  Props:
    - album (Album — TODO: replace with real API type once the Album model exists. Shape for
      now: { id: number; title: string; tagline: string; iconUrl: string; snippetCount: number })
    - progress (number | null): Snippets read out of album.snippetCount. null if not enrolled.
  Layout:
    Left: square icon portion (like SnippetCard).
    Right: album.title, album.tagline as subtitle/CTA, a "{progress} / {snippetCount}" indicator,
      and a ProgressBar (orange-yellow gradient fill) below it.
  Styling:
    Card base, flex row, left square ~80px, right column flex-grow.
    Progress bar fill: linear-gradient(to right, #ff9900, #ffd700) — override ProgressBar's
    default blue fill for this usage.
-->
<script lang="ts">
  import ProgressBar from '$lib/components/ProgressBar.svelte';

  interface Album {
    id: number;
    title: string;
    tagline: string;
    iconUrl: string;
    snippetCount: number;
  }

  export let album: Album;
  export let progress: number | null = null;
</script>

<!-- TODO: Implement the icon + title/tagline/progress layout described above. -->
