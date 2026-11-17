import { existsSync } from "node:fs";
import path from "node:path";

const WEB_DIR = path.resolve(import.meta.dirname, "..");
const SOURCE_PATH = path.join(WEB_DIR, "public", "favicon.png");
const OUTPUT_PATH = path.join(WEB_DIR, "public", "logo.webp");

if (!existsSync(SOURCE_PATH)) {
  throw new Error(
    `Logo source not found: ${path.relative(WEB_DIR, SOURCE_PATH)}`,
  );
}

// 3x the largest on-screen size (128px boot logo) so high-DPI displays stay sharp.
const bytes = await Bun.file(SOURCE_PATH)
  .image()
  .resize(384, 384, { fit: "inside", withoutEnlargement: true })
  .webp({ quality: 90 })
  .write(OUTPUT_PATH);

console.log(
  `Generated ${path.relative(WEB_DIR, OUTPUT_PATH)}: ${bytes} bytes from ${path.relative(WEB_DIR, SOURCE_PATH)}`,
);
