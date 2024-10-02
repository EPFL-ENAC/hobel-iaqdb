import { Variable } from 'src/models';

export interface FileObject extends Blob {
  readonly size: number;
  readonly name: string;
  readonly path: string;
  readonly type: string;
}

export interface DataFile {
  file: FileObject;
  variables: Variable[];
}