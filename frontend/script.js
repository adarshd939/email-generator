document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('content-form');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const generateBtn = document.getElementById('generate-btn');
    const copyBtn = document.getElementById('copy-btn');
    const typeSelect = document.getElementById('type');

    const essayFields = document.getElementById('essay-fields');
    const storyFields = document.getElementById('story-fields');
    const speechFields = document.getElementById('speech-fields');

    // --- Toggle dynamic fields by type ---
    function updateFieldVisibility() {
        const t = typeSelect.value;
        // Default: email shows base fields (goal, recipient, tone, points)
        essayFields.classList.toggle('hidden', t !== 'essay');
        storyFields.classList.toggle('hidden', t !== 'story');
        speechFields.classList.toggle('hidden', t !== 'speech');
    }
    typeSelect.addEventListener('change', updateFieldVisibility);
    updateFieldVisibility();

    // --- Form Submission Handler ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // 1. Get form values
        const type = document.getElementById('type').value;
        const tone = document.getElementById('tone').value;
        const points = document.getElementById('points').value;

        // Base payload and per-type fields
        const payload = { type, tone, points };
        if (type === 'email') {
            payload.goal = document.getElementById('goal').value;
            payload.recipient = document.getElementById('recipient').value;
        } else if (type === 'essay') {
            payload.topic = document.getElementById('topic').value;
            payload.length_words = document.getElementById('essay-length').value;
        } else if (type === 'story') {
            payload.genre = document.getElementById('genre').value;
            payload.setting = document.getElementById('setting').value;
            payload.characters = document.getElementById('characters').value;
            payload.length_words = document.getElementById('story-length').value;
        } else if (type === 'speech') {
            payload.occasion = document.getElementById('occasion').value;
            payload.audience = document.getElementById('audience').value;
            payload.duration_minutes = document.getElementById('speech-duration').value;
        }

        // 2. Update UI for loading state
        resultContainer.classList.remove('hidden');
        loadingIndicator.classList.remove('hidden');
        resultText.textContent = '';
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fa-solid fa-hourglass-half"></i> Generating...';

        try {
            // 3. Make API call
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const contentType = response.headers.get('content-type') || '';
            if (!response.ok) {
                if (contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP ${response.status}`);
                } else {
                    const text = await response.text();
                    throw new Error(`HTTP ${response.status} ${response.statusText}: ${text.slice(0, 200)}`);
                }
            }

            // 4. Display result
            let data;
            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                data = { generated_text: text };
            }
            const text = (data.generated_text || data.generated_email || '').trim();
            resultText.textContent = text;
            resultText.style.color = '';

        } catch (error) {
            resultText.textContent = `Error: ${error.message}`;
            resultText.style.color = '#e94560'; // Style error text
        } finally {
            // 5. Reset UI after completion
            loadingIndicator.classList.add('hidden');
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Generate';
        }
    });
    
    // --- Copy to Clipboard Handler ---
    copyBtn.addEventListener('click', () => {
        if (resultText.textContent) {
            navigator.clipboard.writeText(resultText.textContent)
                .then(() => {
                    // Provide user feedback on successful copy
                    copyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy text: ', err);
                    // Optionally, provide an error message to the user
                    copyBtn.textContent = 'Failed!';
                     setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                    }, 2000);
                });
        }
    });
});