import os
from typing import Dict ,Any , Optional
import yt_dlp

class MediaExtractor:
    def __init__(self,download_dir:str='downloads'):
        self.download_dir = download_dir
        os.makedirs(self.download_dir,exist_ok=True)

    def get_info(selfmurl:str)->Dict[str,Any]:
        """
            Extracts video metadata without downloading bytes.
        """
        ydl_opts ={
            'skip_download':True,
            'extract_flat':False,
            'no_warnings':False,
            'quiet':False
        }

        with yt_dlp.YoutubeDL(ydl_opts)as ydl:
            info = ydl.extract_info(url, download=False)

            formats =[]
            seen_resolutions =set()
            for f in info.get("formats", []):
                #target strams containing the video track
                if f.get('vcodec') !='none' and f.get('resolution'):
                    res = f.get('resolution')
                    if res not in seen_resolutions:
                        seen_resolutions.add(res)
                        formats.append({
                            'format_id':f.get('format_id'),
                            'resolution':res,
                            'ext':f.get('ext'),
                            'file_size':f.get('filesize') or f.get('filesize_approx') or 0     
                        })

            return{
                'title':info.fet('title','untitled'),
                'thumbnail':info.get('thumbnail'),
                'duration':info.get('duration',0),
                'extractor':info.get('extractor_key','Generic'),
                'formats':formats
            }


    def download_media(self,url:str ,job_id:str, format_id: Optional[str]=None) -> str:
        """
        Downlaod the stram and uses FFmpeg to out put a clean MP4 container
        """
        out_tmpl = os.path.join(self.downlaod_dir,f"{job_id}.%(ext)s")
        selected_format = format_id if format_id else "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"

        ydl_opts = {
            'format':selected_format,
            'outtmpl':out_tmpl,
            'merge_output_format':'mp4',
            'no_warnings':True,
            'quite':False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        final_path = os.path.join(self.download_dir,f"{job_id}.mp4")
        if not os.path.exists(final_path):
            raise FileNotFoundError(f"File was not created at expected destination :{final_path}")

        return final_path