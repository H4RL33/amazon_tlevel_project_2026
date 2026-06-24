<!--
  HelpPanel
  Purpose: Content panel for the "Help" destination reachable from the NavBarAvatar
    dropdown.
  Used in: /help
  Props: none -- static FAQ list, hardcoded for now.
  Styling:
    Card base, simple FAQ-style layout (question as heading, answer as body text
    below it).
-->
<script lang="ts">
  const faqs: Array<{ question: string; answer: string }> = [
    {
      question: 'What is a Snippet?',
      answer:
        'A Snippet is a single short-form piece of content — an article, audio clip, or video — that you can read or watch without needing an account.',
    },
    {
      question: 'What is an Album?',
      answer:
        'An Album is a curated set of Snippets forming a learning pathway, like "Cloud Computing T-Level". Enrolling in an Album requires an account so we can track your progress.',
    },
    {
      question: 'Do I need an account to use Living Campus?',
      answer:
        'No — Snippets and Albums are publicly browsable. An account lets you enrol in Albums, track your progress, save Snippets to your Library, and use the social Forum (age permitting).',
    },
  ];
</script>

<div class="help-panel">
  {#each faqs as faq}
    <div class="faq-item">
      <h3>{faq.question}</h3>
      <p>{faq.answer}</p>
    </div>
  {/each}
</div>

<style>
  .help-panel {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 700px;
    margin: 0 auto;
  }

  .faq-item {
    margin-bottom: 1.5rem;
  }

  .faq-item:last-child {
    margin-bottom: 0;
  }

  .faq-item h3 {
    color: #c9d1d9;
    font-size: 1rem;
    margin: 0 0 0.5rem;
  }

  .faq-item p {
    color: #8b949e;
    font-size: 0.875rem;
    line-height: 1.6;
    margin: 0;
  }
</style>
