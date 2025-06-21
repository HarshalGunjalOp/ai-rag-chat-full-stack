import fs from "fs"
import path from "path";

const ROOT_DIR = '.';
const OUTPUT_FILE = 'frontend_flattened.txt';

// Extensions to include
const INCLUDE_EXTENSIONS = new Set([
  '.ts', '.tsx', '.js', '.jsx', '.json',
  '.html', '.css', '.md', '.txt'
]);

// Recursively collect and flatten files
function flattenDirectory(currentPath, writeStream) {
  const entries = fs.readdirSync(currentPath, { withFileTypes: true });

  for (const entry of entries) {
    const entryPath = path.join(currentPath, entry.name);

    // Skip node_modules and hidden directories
    if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;

    if (entry.isDirectory()) {
      flattenDirectory(entryPath, writeStream);
    } else {
      const ext = path.extname(entry.name);
      if (INCLUDE_EXTENSIONS.has(ext)) {
        const relativePath = path.relative(ROOT_DIR, entryPath);
        writeStream.write(`\n\n===== ${relativePath} =====\n\n`);
        const content = fs.readFileSync(entryPath, 'utf-8');
        writeStream.write(content);
      }
    }
  }
}

// Run the script
const writeStream = fs.createWriteStream(OUTPUT_FILE, { encoding: 'utf-8' });
flattenDirectory(ROOT_DIR, writeStream);
writeStream.end(() => {
  console.log(`✅ Flattened code written to ${OUTPUT_FILE}`);
});
