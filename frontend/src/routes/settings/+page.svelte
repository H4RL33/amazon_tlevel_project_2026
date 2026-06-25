<script lang="ts">
  import PageCard from '$lib/components/PageCard.svelte';
  import { requestAvatarUploadUrl, updateAvatar } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  let uploading = false;
  let error: string | null = null;
  let status: string | null = null;
  let fileInput: HTMLInputElement;

  async function handleFileChange() {
    const file = fileInput.files?.[0];
    if (!file) return;

    uploading = true;
    error = null;
    status = 'Uploading...';
    try {
      const { upload_url, key } = await requestAvatarUploadUrl(file.type);

      const putResponse = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      if (!putResponse.ok) {
        throw new Error('Upload to S3 failed');
      }

      const updatedUser = await updateAvatar(key);
      currentUser.set(updatedUser);
      status = 'Profile picture updated.';
    } catch (err) {
      console.error('Avatar upload failed:', err);
      error = 'Could not upload your profile picture. Please try again.';
      status = null;
    } finally {
      uploading = false;
      fileInput.value = '';
    }
  }
</script>

<PageCard as="main">
  <div class="content">
    <h1>Settings</h1>

    <section>
      <h2>Profile picture</h2>
      {#if $currentUser?.avatar_url}
        <img src={$currentUser.avatar_url} alt="Your current profile picture" class="preview" />
      {/if}
      <label for="avatar-input">Upload a new profile picture</label>
      <input
        id="avatar-input"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        bind:this={fileInput}
        on:change={handleFileChange}
        disabled={uploading}
      />
      <p aria-live="polite">{status ?? ''}</p>
      {#if error}
        <p role="alert">{error}</p>
      {/if}
    </section>
  </div>
</PageCard>

<style>
  .content {
    max-width: 900px;
    margin: 0 auto;
  }

  .preview {
    width: 96px;
    height: 96px;
    border-radius: 50%;
    object-fit: cover;
    display: block;
    margin-bottom: 1rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
</style>
