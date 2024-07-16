export function toMaxDecimals(x: number | null, n: number): number | null {
  if (x === null) {
    return null;
  }
  return +x.toFixed(n);
}

export function toFixed(x: number | null, n: number): string | null {
  if (x === null) {
    return null;
  }
  return x.toFixed(n);
}

const scale_labels: { [Key: string]: string } = {
  '1.0': '1',
  '0.5': '1/2',
  '0.333': '1/3',
  '0.25': '1/4',
  '0.667': '2/3',
  '0.1': '1/10',
};

export function testScaleLabel(scale: string | number | null): string {
  return scale === null ? 'N/A' : scale_labels[scale + ''] || scale + '';
}

export function testScaleValue(label: string): number {
  const scale = Object.keys(scale_labels).find(
    (key) => scale_labels[key] === label
  );
  return parseFloat(scale || label);
}

export function makeLiteralLabel(values: number[]): string {
  const last = values.pop();
  if (values.length === 0) {
    return last + '';
  }
  return values.join(', ') + ' and ' + last;
}