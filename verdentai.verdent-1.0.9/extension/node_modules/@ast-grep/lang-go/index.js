const path = require('node:path')
const libPath = path.join(__dirname, 'parser.so')

module.exports = {
  libraryPath: libPath,
  extensions: ['go'],
  languageSymbol: 'tree_sitter_go',
  expandoChar: 'µ',
}
