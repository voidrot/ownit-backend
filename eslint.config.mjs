// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  // Your custom configs here
  {
    rules: {
      'semi': ['error', 'never'],
      'quotes': ['error', 'single']
    }
  }
)
