package rec.ai;

import android.content.ContentValues;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;

@CapacitorPlugin(name = "Downloader")
public class DownloaderPlugin extends Plugin {

    @PluginMethod
    public void downloadFile(PluginCall call) {
        String base64Data = call.getString("data");
        String filename   = call.getString("filename", "document.pdf");
        String mimeType   = call.getString("mimeType", "application/pdf");

        if (base64Data == null || base64Data.isEmpty()) {
            call.reject("No data provided");
            return;
        }

        try {
            byte[] bytes = Base64.decode(base64Data, Base64.DEFAULT);

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                // Android 10+ — MediaStore.Downloads (no storage permission needed)
                Context ctx = getContext();
                ContentValues cv = new ContentValues();
                cv.put(MediaStore.Downloads.DISPLAY_NAME, filename);
                cv.put(MediaStore.Downloads.MIME_TYPE, mimeType);
                cv.put(MediaStore.Downloads.IS_PENDING, 1);

                Uri collection = MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY);
                Uri fileUri = ctx.getContentResolver().insert(collection, cv);

                if (fileUri == null) {
                    call.reject("Could not create entry in Downloads");
                    return;
                }

                try (OutputStream out = ctx.getContentResolver().openOutputStream(fileUri)) {
                    if (out == null) {
                        call.reject("Could not open output stream");
                        return;
                    }
                    out.write(bytes);
                }

                // Mark as complete — file is now visible in Downloads
                cv.clear();
                cv.put(MediaStore.Downloads.IS_PENDING, 0);
                ctx.getContentResolver().update(fileUri, cv, null, null);

            } else {
                // Android 9 and below — write directly to the public Downloads dir
                File dir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
                if (!dir.exists()) dir.mkdirs();
                File out = new File(dir, filename);
                try (FileOutputStream fos = new FileOutputStream(out)) {
                    fos.write(bytes);
                }
            }

            JSObject result = new JSObject();
            result.put("success", true);
            result.put("filename", filename);
            call.resolve(result);

        } catch (Exception e) {
            call.reject("Download failed: " + e.getMessage());
        }
    }
}
