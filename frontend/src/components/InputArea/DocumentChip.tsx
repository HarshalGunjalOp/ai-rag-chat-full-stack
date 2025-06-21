import {XMarkIcon} from '@heroicons/react/24/solid';

export default function DocumentChip({
  name,
  onRemove,
}: {
  name: string;
  onRemove?: () => void;
}) {
  return (
    <span className="document-chip">
      <span className="filename truncate">{name}</span>
      {onRemove && (
        <button onClick={onRemove} className="remove-btn">
          <XMarkIcon className="w-3 h-3" />
        </button>
      )}
    </span>
  );
}
