<script lang="ts">
  import { page } from '$app/stores';
  import PageCard from '$lib/components/PageCard.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import type { SidebarSection } from '$lib/components/Sidebar.svelte';
  import Button from '$lib/components/Button.svelte';
  import AvatarBadge from '$lib/components/AvatarBadge.svelte';
  import TextInput from '$lib/components/TextInput.svelte';
  import { requestAvatarUploadUrl, updateAvatar, updateUsername } from '$lib/api/users';
  import { currentUser } from '$lib/stores/user';

  const MAX_BYTES = 2 * 1024 * 1024; // 2 MiB

  let uploading = false;
  let error: string | null = null;
  let status: string | null = null;
  let fileInput: HTMLInputElement;

  let usernameValue = $currentUser?.username ?? '';
  let usernameStatus: string | null = null;
  let usernameError: string | null = null;
  let savingUsername = false;

  $: if ($currentUser) usernameValue = $currentUser.username ?? '';

  const settingsSections: SidebarSection[] = [
    { links: [{ label: 'Personalisation', href: '/settings' }] },
  ];

  async function handleSaveUsername() {
    if (!usernameValue.trim()) return;
    savingUsername = true;
    usernameStatus = null;
    usernameError = null;
    try {
      const updated = await updateUsername(usernameValue.trim());
      currentUser.set(updated);
      usernameStatus = 'Username updated.';
    } catch (err) {
      const msg = err instanceof Error ? err.message : '';
      usernameError = msg || 'Could not update username. Please try again.';
    } finally {
      savingUsername = false;
    }
  }

  function processImage(file: File): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const objectUrl = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => {
        URL.revokeObjectURL(objectUrl);
        const cropSize = Math.min(img.naturalWidth, img.naturalHeight);
        const sx = (img.naturalWidth - cropSize) / 2;
        const sy = (img.naturalHeight - cropSize) / 2;
        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 800;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          reject(new Error('Could not get canvas context'));
          return;
        }
        ctx.drawImage(img, sx, sy, cropSize, cropSize, 0, 0, 800, 800);
        canvas.toBlob(
          (blob) => {
            if (blob) resolve(blob);
            else reject(new Error('canvas.toBlob returned null'));
          },
          'image/webp',
          0.9
        );
      };
      img.onerror = () => {
        URL.revokeObjectURL(objectUrl);
        reject(new Error('Image failed to load'));
      };
      img.src = objectUrl;
    });
  }

  async function handleFileChange() {
    const file = fileInput.files?.[0];
    if (!file) return;

    error = null;
    status = null;

    if (file.size > MAX_BYTES) {
      error = 'File must be under 2 MB.';
      fileInput.value = '';
      return;
    }

    uploading = true;
    status = 'Processing...';
    try {
      const blob = await processImage(file);
      status = 'Uploading...';

      const { upload_url, key } = await requestAvatarUploadUrl('image/webp');

      const putResponse = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': 'image/webp' },
        body: blob,
      });
      if (!putResponse.ok) {
        throw new Error('Upload to S3 failed');
      }

      const updatedUser = await updateAvatar(key);
      currentUser.set(updatedUser);
      status = 'Profile picture updated.';
    } catch (err) {
      console.error('Avatar upload failed:', err);
      const msg = err instanceof Error ? err.message : '';
      const isProcessingError =
        msg === 'Could not get canvas context' ||
        msg === 'canvas.toBlob returned null' ||
        msg === 'Image failed to load';
      if (isProcessingError) {
        error = 'Could not process image. Please try a different file.';
      } else {
        error = 'Could not upload your profile picture. Please try again.';
      }
      status = null;
    } finally {
      uploading = false;
      fileInput.value = '';
    }
  }
</script>

<div class="settings-page">
  <Sidebar sections={settingsSections} activeHref={$page.url.pathname} ariaLabel="Settings sections" />

  <PageCard as="main">
    <h1>Personalisation</h1>
    <hr />

    <div class="upload-row">
      <label for="avatar-trigger">Upload a profile picture</label>
      <div class="upload-controls">
        {#if $currentUser}
          <AvatarBadge user={$currentUser} size="32px" />
        {/if}
        <Button
          variant="secondary"
          disabled={uploading}
          aria-label="Upload profile picture"
          on:click={() => fileInput.click()}
        >
          Choose file
        </Button>
        <input
          type="file"
          id="avatar-trigger"
          accept="image/jpeg,image/png,image/webp"
          bind:this={fileInput}
          on:change={handleFileChange}
          disabled={uploading}
          style="display: none;"
        />
      </div>
    </div>

    <div class="field-row">
      <label for="username-input">Username</label>
      <div class="field-controls">
        <TextInput
          id="username-input"
          bind:value={usernameValue}
          placeholder="e.g. harley_welsh"
          disabled={savingUsername}
        />
        <Button
          variant="secondary"
          disabled={savingUsername || !usernameValue.trim()}
          on:click={handleSaveUsername}
        >
          {savingUsername ? 'Saving…' : 'Save'}
        </Button>
      </div>
    </div>
    {#if usernameStatus}
      <p aria-live="polite" class="status">{usernameStatus}</p>
    {/if}
    {#if usernameError}
      <p role="alert" class="error">{usernameError}</p>
    {/if}
    <hr />

    <p aria-live="polite" class="status">{status ?? ''}</p>
    {#if error}
      <p role="alert" class="error">{error}</p>
    {/if}
  </PageCard>
</div>

<style>
  .settings-page {
    display: flex;
    gap: var(--gap-inner);
    height: 100%;
  }

  .settings-page > :global(aside.page-card) {
    flex: 0 0 288px;
  }

  .settings-page > :global(main.page-card) {
    flex: 1 1 auto;
    min-width: 0;
  }

  h1 {
    margin: 0 0 0.75rem;
    font-size: 1.25rem;
    font-weight: 700;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  hr {
    border: none;
    border-top: 1px solid #e2e2dc;
    margin: 0 0 1.5rem;
  }

  .upload-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  label {
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.875rem;
    color: #232f3e;
  }

  .upload-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .field-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .field-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .status {
    font-size: 0.875rem;
    color: #5a6472;
    margin: 0.75rem 0 0;
    min-height: 1.25em;
    font-family: 'Ubuntu', sans-serif;
  }

  .error {
    font-size: 0.875rem;
    color: #ef4444;
    margin: 0.5rem 0 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
