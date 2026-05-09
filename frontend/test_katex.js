import { marked } from 'marked';
import markedKatex from 'marked-katex-extension';

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

const text = "（$\\boldsymbol{\\Sigma}_{\\text{low-rank}} = \\sum_{i=1}^{6} \\lambda_i \\mathbf{u}_i \\mathbf{u}_i^\\top$）";
console.log("Original Input:", text);
console.log("Parsed Output:", marked.parse(text));
