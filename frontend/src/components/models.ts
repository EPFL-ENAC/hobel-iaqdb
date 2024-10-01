export interface FileObject extends Blob {
  readonly size: number;
  readonly name: string;
  readonly path: string;
  readonly type: string;
}

export interface FieldSpec {
  field: string;
  variable: string;
  format?: string;
}

export interface DataFile {
  file: FileObject;
  dictionary: FieldSpec[];
}