#!/usr/bin/env node
import fs from 'fs/promises'
import path from 'path'
import { countTokens } from 'gpt-tokenizer'

const args = process.argv.slice(2)

function readArg(flag) {
  const idx = args.indexOf(flag)
  if (idx === -1) return null
  return args[idx + 1] ?? null
}

function hasFlag(flag) {
  return args.includes(flag)
}

const model = readArg('--model') || 'gpt-4o'
const inputFile = readArg('--input')
const outputFile = readArg('--output')
const inputTextArg = readArg('--input-text')
const outputTextArg = readArg('--output-text')
const jsonOut = hasFlag('--json')

async function loadText(value) {
  if (!value) return ''
  return value
}

async function loadFile(filePath) {
  if (!filePath) return ''
  const resolved = path.resolve(process.cwd(), filePath)
  return fs.readFile(resolved, 'utf-8')
}

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = ''
    process.stdin.setEncoding('utf-8')
    process.stdin.on('data', chunk => {
      data += chunk
    })
    process.stdin.on('end', () => resolve(data))
    process.stdin.on('error', err => reject(err))
  })
}

async function getModelEstimator() {
  try {
    const mod = await import(`gpt-tokenizer/model/${model}`)
    return mod.estimateCost
  } catch (err) {
    return null
  }
}

function summarizeCost(estimate, label) {
  if (!estimate) return null
  return {
    label,
    main: estimate.main ?? null,
    batch: estimate.batch ?? null,
  }
}

async function main() {
  let inputText = ''
  let outputText = ''

  if (inputTextArg) {
    inputText = await loadText(inputTextArg)
  } else if (inputFile) {
    inputText = await loadFile(inputFile)
  }

  if (outputTextArg) {
    outputText = await loadText(outputTextArg)
  } else if (outputFile) {
    outputText = await loadFile(outputFile)
  }

  if (!inputText && !outputText) {
    const stdin = await readStdin()
    inputText = stdin
  }

  const inputTokens = inputText ? countTokens(inputText, model) : 0
  const outputTokens = outputText ? countTokens(outputText, model) : 0
  const estimateCost = await getModelEstimator()

  const inputCost = estimateCost ? summarizeCost(estimateCost(inputTokens), 'input') : null
  const outputCost = estimateCost ? summarizeCost(estimateCost(outputTokens), 'output') : null

  const payload = {
    model,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    total_tokens: inputTokens + outputTokens,
    input_cost: inputCost,
    output_cost: outputCost,
  }

  if (jsonOut) {
    process.stdout.write(JSON.stringify(payload, null, 2))
    return
  }

  console.log(`Model: ${model}`)
  console.log(`Input tokens: ${inputTokens}`)
  console.log(`Output tokens: ${outputTokens}`)
  console.log(`Total tokens: ${inputTokens + outputTokens}`)
  if (inputCost?.main?.input !== undefined) {
    console.log(`Estimated input cost (main): ${inputCost.main.input}`)
  }
  if (outputCost?.main?.output !== undefined) {
    console.log(`Estimated output cost (main): ${outputCost.main.output}`)
  }
  if (!estimateCost) {
    console.log('Cost estimation unavailable for this model.')
  }
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
