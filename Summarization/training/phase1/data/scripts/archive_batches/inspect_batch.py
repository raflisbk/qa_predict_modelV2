import pandas as pd

# Load data
df = pd.read_csv('./data/step1.csv')
print(f'Total rows: {len(df)}')

# Get first batch
batch = df.head(50)
print(f'\nFirst batch: {len(batch)} rows')
print(f'\nColumns: {list(batch.columns)}')

# Show sample
print('\n' + '='*60)
print('SAMPLE ROW 0:')
print('='*60)
print(f"\nStudent Input:\n{batch.iloc[0]['student_input']}")
print(f"\n\nPrompt for AI:\n{batch.iloc[0]['prompt_for_gemini']}")

# Save first batch for processing
batch[['student_input', 'prompt_for_gemini']].to_csv('./data/batch_first_50.csv', index=False)
print(f"\n✓ Saved first 50 rows to ./data/batch_first_50.csv")
