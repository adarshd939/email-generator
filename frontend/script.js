document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('content-form');
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const generateBtn = document.getElementById('generate-btn');
    const copyBtn = document.getElementById('copy-btn');
    const typeSelect = document.getElementById('type');

    const emailFields = document.getElementById('email-fields');
    const essayFields = document.getElementById('essay-fields');
    const storyFields = document.getElementById('story-fields');
    const speechFields = document.getElementById('speech-fields');

    // --- Toggle dynamic fields by type ---
    function updateFieldVisibility() {
        const t = typeSelect.value;
        // Show/hide content-specific fields
        emailFields.classList.toggle('hidden', t !== 'email');
        essayFields.classList.toggle('hidden', t !== 'essay');
        storyFields.classList.toggle('hidden', t !== 'story');
        speechFields.classList.toggle('hidden', t !== 'speech');
        
        // Update required attributes based on content type
        updateRequiredFields(t);
    }

    // --- Update required field attributes ---
    function updateRequiredFields(contentType) {
        // Reset all fields to not required first
        const allFields = ['goal', 'recipient', 'topic', 'genre', 'setting', 'characters', 'occasion', 'audience'];
        allFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.removeAttribute('required');
            }
        });

        // Set required fields based on content type
        if (contentType === 'email') {
            document.getElementById('goal').setAttribute('required', '');
            document.getElementById('recipient').setAttribute('required', '');
        } else if (contentType === 'essay') {
            document.getElementById('topic').setAttribute('required', '');
        } else if (contentType === 'story') {
            document.getElementById('genre').setAttribute('required', '');
            document.getElementById('setting').setAttribute('required', '');
            document.getElementById('characters').setAttribute('required', '');
        } else if (contentType === 'speech') {
            document.getElementById('occasion').setAttribute('required', '');
            document.getElementById('audience').setAttribute('required', '');
        }
    }
    typeSelect.addEventListener('change', updateFieldVisibility);
    updateFieldVisibility();

    // --- Form Submission Handler ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // 1. Get form values and build payload
        const type = document.getElementById('type').value;
        const tone = document.getElementById('tone').value;
        const points = document.getElementById('points').value;

        // Validate required common fields
        if (!type || !tone || !points.trim()) {
            alert('Please fill in all required fields.');
            return;
        }

        // Base payload with common fields
        const payload = { 
            type, 
            tone, 
            points: points.trim() 
        };

        // Add type-specific fields with proper validation
        if (type === 'email') {
            const goal = document.getElementById('goal').value.trim();
            const recipient = document.getElementById('recipient').value.trim();
            if (!goal || !recipient) {
                alert('Please fill in the email goal and recipient.');
                return;
            }
            payload.goal = goal;
            payload.recipient = recipient;
        } else if (type === 'essay') {
            const topic = document.getElementById('topic').value.trim();
            if (!topic) {
                alert('Please enter an essay topic.');
                return;
            }
            payload.topic = topic;
            const length = document.getElementById('essay-length').value;
            if (length) payload.length_words = parseInt(length);
        } else if (type === 'story') {
            const genre = document.getElementById('genre').value.trim();
            const setting = document.getElementById('setting').value.trim();
            const characters = document.getElementById('characters').value.trim();
            if (!genre || !setting || !characters) {
                alert('Please fill in the story genre, setting, and characters.');
                return;
            }
            payload.genre = genre;
            payload.setting = setting;
            payload.characters = characters;
            const length = document.getElementById('story-length').value;
            if (length) payload.length_words = parseInt(length);
        } else if (type === 'speech') {
            const occasion = document.getElementById('occasion').value.trim();
            const audience = document.getElementById('audience').value.trim();
            if (!occasion || !audience) {
                alert('Please fill in the speech occasion and audience.');
                return;
            }
            payload.occasion = occasion;
            payload.audience = audience;
            const duration = document.getElementById('speech-duration').value;
            if (duration) payload.duration_minutes = parseInt(duration);
        }

        // 2. Update UI for loading state
        resultContainer.classList.remove('hidden');
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